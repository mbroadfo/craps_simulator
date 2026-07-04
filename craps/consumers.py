"""Event-stream consumers (Phase 1, Step 4a).

Statistics, play-by-play, and roll history observe the engine's event
stream instead of being called directly. Wiring lives in
``attach_default_consumers``; the engine emits facts and never talks to
these objects again.

Fidelity notes (v1 observed behavior is the spec, verified by the golden
stats-parity gate):
- ``update_shooter_stats`` is a no-op in real sessions (``set_shooter`` has
  no callers, so ``shooter_num`` is always None). The call is preserved.
- ``record_seven_out`` fires twice per seven-out: once from
  ``GameState.update_state`` (still direct) and once here via the SevenOut
  event — exactly as the pre-refactor engine double-called it.
- The SevenOut handler overwrites ``shooter_stats[shooter_index]`` with the
  bankroll-delta dict, clobbering any roll-tracking dict — a v1 quirk.
"""
from __future__ import annotations
from typing import Any, Callable, Dict, List, TYPE_CHECKING

from craps.events import (
    EventBus,
    BetsRequested,
    DiceRolled,
    BetResolved,
    NumberHit,
    GameStateChanged,
    BankrollsUpdated,
    RiskUpdated,
    SevenOut,
)

if TYPE_CHECKING:
    from craps.statistics import Statistics
    from craps.play_by_play import PlayByPlay
    from craps.player import Player


class StatsConsumer:
    """Applies the event stream to a Statistics object with the same
    mutations the engine used to perform inline."""

    def __init__(self, stats: "Statistics", players_provider: Callable[[], List["Player"]]) -> None:
        self.stats = stats
        self.players_provider = players_provider

    def subscribe(self, bus: EventBus) -> None:
        bus.subscribe(DiceRolled, self._on_dice_rolled)      # type: ignore[arg-type]
        bus.subscribe(BetResolved, self._on_bet_resolved)    # type: ignore[arg-type]
        bus.subscribe(BankrollsUpdated, self._on_bankrolls)  # type: ignore[arg-type]
        bus.subscribe(RiskUpdated, self._on_risk)            # type: ignore[arg-type]
        bus.subscribe(SevenOut, self._on_seven_out)          # type: ignore[arg-type]

    def _on_dice_rolled(self, e: DiceRolled) -> None:
        players = self.players_provider()
        shooter = players[e.shooter_index % len(players)]
        self.stats.update_rolls(total=e.total, table_risk=e.table_risk)
        self.stats.update_shooter_stats(shooter)

    def _on_bet_resolved(self, e: BetResolved) -> None:
        if e.status in ("won", "lost"):
            self.stats.total_amount_bet += e.amount
            player_stats = self.stats.player_stats.get(e.player_name)
            if player_stats:
                player_stats["bets_settled"] += 1
                if e.status == "won":
                    self.stats.total_amount_won += e.win_payout
                    player_stats["bets_won"] += 1
                elif e.status == "lost":
                    self.stats.total_amount_lost += e.amount

    def _on_bankrolls(self, e: BankrollsUpdated) -> None:
        s = self.stats
        s.player_bankrolls = [balance for _, balance in e.bankrolls]
        s.highest_bankroll = max(s.player_bankrolls)
        s.lowest_bankroll = min(s.player_bankrolls)
        for name, balance in e.bankrolls:
            if name not in s.bankroll_history:
                s.bankroll_history[name] = []
            s.bankroll_history[name].append(balance)
            if name in s.player_stats:
                ps = s.player_stats[name]
                ps["highest_bankroll"] = max(ps["highest_bankroll"], balance)
                ps["lowest_bankroll"] = min(ps["lowest_bankroll"], balance)
            if balance > s.session_highest_bankroll:
                s.session_highest_bankroll = balance
            if balance < s.session_lowest_bankroll:
                s.session_lowest_bankroll = balance

    def _on_risk(self, e: RiskUpdated) -> None:
        for name, at_risk in e.at_risk:
            if name not in self.stats.at_risk_history:
                self.stats.at_risk_history[name] = []
            self.stats.at_risk_history[name].append(at_risk)

    def _on_seven_out(self, e: SevenOut) -> None:
        if e.shooter_results:
            self.stats.shooter_stats[e.shooter_index] = dict(e.shooter_results)
        self.stats.record_seven_out()


class PlayByPlayConsumer:
    """Writes the engine-level narration lines the engine used to write."""

    def __init__(self, play_by_play: "PlayByPlay") -> None:
        self.play_by_play = play_by_play

    def subscribe(self, bus: EventBus) -> None:
        bus.subscribe(BetsRequested, self._on_bets_requested)  # type: ignore[arg-type]
        bus.subscribe(DiceRolled, self._on_dice_rolled)        # type: ignore[arg-type]
        bus.subscribe(NumberHit, self._on_number_hit)          # type: ignore[arg-type]
        bus.subscribe(GameStateChanged, self._on_state)        # type: ignore[arg-type]

    def _on_bets_requested(self, e: BetsRequested) -> None:
        self.play_by_play.write("  ---------- Place Your Bets! -------------")

    def _on_dice_rolled(self, e: DiceRolled) -> None:
        self.play_by_play.write(
            f"  ---------- Shooter {e.shooter_index} ({e.shooter_name}) — Roll #{e.roll_number} ----------"
        )
        puck_state = "Puck OFF" if e.phase == "come-out" else f"Puck ON {e.point}"
        self.play_by_play.write(
            f"  🎲 Roll #{e.roll_number} → {e.dice} = {e.total} ({puck_state})"
        )

    def _on_number_hit(self, e: NumberHit) -> None:
        self.play_by_play.write(e.message)

    def _on_state(self, e: GameStateChanged) -> None:
        self.play_by_play.write(e.message)


class RollHistoryConsumer:
    """Appends each roll to the session roll-history list."""

    def __init__(self, roll_history: List[Dict[str, Any]]) -> None:
        self.roll_history = roll_history

    def subscribe(self, bus: EventBus) -> None:
        bus.subscribe(DiceRolled, self._on_dice_rolled)  # type: ignore[arg-type]

    def _on_dice_rolled(self, e: DiceRolled) -> None:
        self.roll_history.append({
            "shooter_num": e.shooter_index + 1,
            "roll_number": e.roll_number,
            "dice": list(e.dice),
            "total": e.total,
            "phase": e.phase,
            "point": e.point,
        })


def attach_default_consumers(engine: Any) -> None:
    """Wire the standard consumers to an initialized engine's bus.

    Subscription order matters: stats first, so play-by-play narration on
    the same event observes updated statistics if it ever needs them.
    """
    StatsConsumer(engine.stats, engine.player_lineup.get_active_players_list).subscribe(engine.events)
    PlayByPlayConsumer(engine.play_by_play).subscribe(engine.events)
    RollHistoryConsumer(engine.roll_history).subscribe(engine.events)
