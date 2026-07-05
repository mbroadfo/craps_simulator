"""TableRunner: owns one engine instance and drives the roll loop (Phase 2, Step 0).

The session loop extracted from ``simulate_single_session`` so it exists
in exactly one place (D4) — that function now delegates here, which puts
this runner under every Phase 1 gate. Synchronous for now; Step 1 wraps
it in an async task. The engine is called exactly as before and stays
untouched.
"""
from __future__ import annotations
import time
from pathlib import Path
from typing import Any, Dict, Optional, Sequence, Tuple, Union

from craps.craps_engine import CrapsEngine, PostRollSummary
from craps.player import Player
from craps.session_recorder import SessionRecorder
from craps.statistics import Statistics

#: (player_name, strategy_name) pairs; strategy names are PlayerLineup keys.
LineupConfig = Sequence[Tuple[str, str]]


class TableRunner:
    def __init__(
        self,
        table_id: str = "table-1",
        players: Optional[LineupConfig] = None,
        house_rules: Optional[Dict[str, Any]] = None,
        roll_delay_ms: int = 0,
        max_shooters: int = 10,
        max_rolls: Optional[int] = None,
        dice_seed: Optional[int] = None,
        record: bool = False,
        sessions_dir: Union[str, Path] = "sessions",
        quiet_mode: bool = True,
    ) -> None:
        self.table_id = table_id
        self.players = players  # None → ACTIVE_PLAYERS from config.py
        self.house_rules = house_rules
        self.roll_delay_ms = roll_delay_ms
        self.max_shooters = max_shooters
        self.max_rolls = max_rolls
        self.dice_seed = dice_seed
        self.engine = CrapsEngine(quiet_mode=quiet_mode)
        self.recorder: Optional[SessionRecorder] = None
        if record:
            # Before setup_session, so SessionStarted lands in the log.
            recorder = SessionRecorder(table_id, sessions_dir)
            recorder.subscribe(self.engine.events)
            self.recorder = recorder

    def start_session(self) -> None:
        """Initialize the engine, seat the lineup, and assign the first shooter."""
        engine = self.engine
        if not engine.setup_session(
            house_rules_dict=self.house_rules,
            num_shooters=self.max_shooters,
            dice_mode="live",
            dice_seed=self.dice_seed,
        ):
            raise RuntimeError("Failed to initialize session.")

        if self.players is None:
            engine.add_players_from_config()
        else:
            self._add_players()

        engine.lock_session()
        engine.assign_next_shooter()

    def roll_once(self) -> PostRollSummary:
        """One complete roll cycle: accept → roll → resolve → refresh → post-roll.

        The single place the per-roll sequence lives; the sync run() loop
        and the async TableSession driver both call it.
        """
        engine = self.engine
        engine.accept_bets()
        outcome = engine.roll_dice()
        if engine.game_state is None:
            raise RuntimeError("Game state not initialized")
        prev_phase = engine.game_state.phase
        engine.resolve_bets(outcome)
        engine.refresh_bet_statuses()
        engine.log_player_bets()
        return engine.handle_post_roll(outcome, prev_phase)

    def run(self) -> Statistics:
        self.start_session()

        rolls = 0
        roll_limit_hit = False
        try:
            for _ in range(self.max_shooters):
                while True:
                    if self.roll_delay_ms:
                        time.sleep(self.roll_delay_ms / 1000)
                    summary = self.roll_once()
                    rolls += 1
                    if self.max_rolls is not None and rolls >= self.max_rolls:
                        roll_limit_hit = True
                        break
                    if summary.new_shooter_assigned:
                        break
                if roll_limit_hit:
                    break
        except KeyboardInterrupt:
            pass  # stop cleanly; finalize what we have

        return self.finalize()

    def _add_players(self) -> None:
        engine = self.engine
        if engine.player_lineup is None:
            raise RuntimeError("Session must be initialized before adding players.")
        assert self.players is not None
        players = [
            Player(name=name, strategy_name=strategy_name)
            for name, strategy_name in self.players
        ]
        engine.player_lineup.assign_strategies(players)
        if engine.stats:
            engine.stats.initialize_player_stats(players)
            engine.stats.num_players = len(players)

    def finalize(self) -> Statistics:
        engine = self.engine
        try:
            if engine.stats is None:
                raise RuntimeError("Statistics not initialized.")
            if engine.roll_history_manager is None:
                raise RuntimeError("Roll history manager not initialized.")
            if engine.player_lineup is None:
                raise RuntimeError("Player lineup not initialized.")
            return engine.finalize_session(
                stats=engine.stats,
                dice_mode="live",
                roll_history=engine.roll_history,
                roll_history_manager=engine.roll_history_manager,
                play_by_play=engine.play_by_play,
                players=engine.player_lineup.get_active_players_list(),
            )
        finally:
            # No-op if SessionFinalized already closed it.
            if self.recorder is not None:
                self.recorder.close()
