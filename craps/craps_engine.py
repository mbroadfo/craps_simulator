from __future__ import annotations
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from typing import Optional, Any, NamedTuple
from config import HOUSE_RULES, ACTIVE_PLAYERS
from craps.house_rules import HouseRules
from craps.log_manager import LogManager
from craps.play_by_play import PlayByPlay
from craps.rules_engine import RulesEngine
from craps.session_initializer import InitializeSession
from craps.lineup import PlayerLineup
from craps.dice import Dice
from craps.table import Table
from craps.roll_history_manager import RollHistoryManager
from craps.statistics import Statistics
from craps.game_state import GameState
from craps.player import Player
from craps.view_log import InteractiveLogViewer
from craps.statistics_report import StatisticsReport
from craps.visualizer import Visualizer
from craps.events import (
    EventBus,
    SessionStarted,
    ShooterAssigned,
    BetsRequested,
    BetPlaced,
    BetMoved,
    BetAdjusted,
    BetStatusChanged,
    DiceRolled,
    BetResolved,
    NumberHit,
    GameStateChanged,
    BankrollsUpdated,
    RiskUpdated,
    PointEstablished,
    PointHit,
    SevenOut,
    SessionFinalized,
)

#: Bet types whose ``number`` is assigned after placement (Come/Don't Come
#: travel; odds attaching to the point). Field also mutates ``number`` on a
#: win, but there it records the rolled total, not a position — excluded.
_NUMBER_FILL_BET_TYPES = frozenset({
    "Come", "Don't Come",
    "Pass Line Odds", "Don't Pass Odds", "Come Odds", "Don't Come Odds",
})
from craps.consumers import attach_default_consumers

class PostRollSummary(NamedTuple):
    total: int
    seven_out: bool
    point_was_hit: bool
    transitioned: bool
    puck_on: bool
    new_shooter_assigned: bool
    shooter_continues: bool


class CrapsEngine:
    def __init__(self, quiet_mode: bool = False) -> None:
        self.house_rules: Optional[HouseRules] = None
        self.table: Optional[Table] = None
        self.dice: Optional[Dice] = None
        self.game_state: Optional[GameState] = None
        self.roll_history_manager: Optional[RollHistoryManager] = None
        self.roll_history: list[dict[str, Any]] = []
        self.log_manager: Optional[LogManager] = None
        self.rules_engine: Optional[RulesEngine] = None
        self.stats: Optional[Statistics] = None
        self.player_lineup: Optional[PlayerLineup] = None
        self.shooter_index: int = 0
        self.initialized: bool = False
        self.locked: bool = False
        self._quiet_mode: bool = quiet_mode
        self._visualizer: Optional[Visualizer] = None
        self._report_writer: Optional[StatisticsReport] = None
        self.play_by_play = PlayByPlay(engine=self)
        self.events = EventBus()
        
    @property
    def quiet_mode(self) -> bool:
        return self._quiet_mode

    @property
    def visualizer(self) -> Visualizer:
        if self._visualizer is None:
            self._visualizer = Visualizer(self.stats)
        return self._visualizer

    @property
    def report_writer(self) -> StatisticsReport:
        if self._report_writer is None:
            self._report_writer = StatisticsReport()
        return self._report_writer

    def setup_session(
        self,
        house_rules_dict: Optional[dict[str, Any]] = None,
        num_shooters: int = 10,
        num_players: int = 0,
        dice_mode: str = "live", # "live" or "history"
        roll_history_file: Optional[str] = None,
        dice_seed: Optional[int] = None,
    ) -> bool:
        """
        Initializes core game components and prepares the session.
        """
        self.house_rules = HouseRules(house_rules_dict or HOUSE_RULES)
        self.play_by_play = PlayByPlay(engine=self)
        self.log_manager = LogManager()
        self.rules_engine = RulesEngine()
        self.player_lineup = PlayerLineup(self.house_rules, None, self.play_by_play, self.rules_engine)

        # ✅ Initialize Dice
        if dice_mode == "history" and roll_history_file:
            self.dice = Dice(roll_history_file)
        else:
            self.dice = Dice(seed=dice_seed)

        # ✅ Initialize Session
        session_initializer = InitializeSession(
            dice_mode=dice_mode,
            house_rules=self.house_rules,
            play_by_play=self.play_by_play,
            log_manager=self.log_manager,
            rules_engine=self.rules_engine,
            player_lineup=self.player_lineup,
            quiet_mode=self.quiet_mode
        )

        session_data = session_initializer.prepare_session(num_shooters, num_players)

        if session_data is None:
            return False

        (
            self.house_rules,
            self.table,
            self.roll_history_manager,
            self.log_manager,
            self.play_by_play,
            self.stats,
            self.game_state
        ) = session_data

        if not getattr(self, "_consumers_attached", False):
            attach_default_consumers(self)
            self._consumers_attached = True

        self.initialized = True
        self.events.publish(SessionStarted(num_shooters=num_shooters))
        return True

    def add_players_from_config(self) -> int:
        """
        Add players based on the ACTIVE_PLAYERS dict in config.py.
        UI or CLI setup should modify this config ahead of time.
        """
        if not self.player_lineup:
            raise RuntimeError("Session must be initialized before adding players.")

        players = [
            Player(name=player_name, strategy_name=strategy_name)
            for player_name, (strategy_name, enabled) in ACTIVE_PLAYERS.items() if enabled
        ]

        self.player_lineup.assign_strategies(players)

        if self.stats:
            self.stats.initialize_player_stats(players)
            self.stats.num_players = len(players)

        return len(players)

    def lock_session(self) -> None:
        """
        Lock the session to prevent further changes to players or rules.
        """
        if not self.initialized:
            raise RuntimeError("Session must be initialized before it can be locked.")
        self.locked = True
        
        if not self.player_lineup or not self.play_by_play:
            raise RuntimeError("SessionManager is missing required components.")

    def accept_bets(self) -> int:
        if not self.locked:
            raise RuntimeError("Session must be locked before accepting bets.")
        if not self.play_by_play or not self.game_state or not self.table or not self.player_lineup:
            return 0

        self.events.publish(BetsRequested())
        total_bets = 0

        # Strategy status specs at collection time reshape live bets in
        # place (e.g. hardway reactivation) without going through place_bet.
        statuses_before = [(bet, bet.status) for bet in self.table.bets]

        for player in self.player_lineup.get_active_players_list():
            if not player.betting_strategy:
                continue

            bets = player.betting_strategy.place_bets(
                game_state=self.game_state,
                player=player,
                table=self.table
            )

            if bets:
                on_table_before = {id(b) for b in self.table.bets}
                success = player.place_bet(
                    bets,
                    table=self.table,
                    phase=self.game_state.phase,
                    play_by_play=self.play_by_play
                )
                if success:
                    total_bets += len(bets) if isinstance(bets, list) else 1
                # Publish what actually landed, not what was requested:
                # place_bet aborts mid-list on a failure without rolling
                # back the bets already placed, and those chips are live.
                for bet in self.table.bets:
                    if id(bet) not in on_table_before:
                        self.events.publish(BetPlaced(
                            player_name=player.name,
                            bet_type=bet.bet_type,
                            amount=bet.amount,
                            number=bet.number,
                        ))

        for bet, old_status in statuses_before:
            if bet.status != old_status:
                self.events.publish(BetStatusChanged(
                    player_name=bet.owner.name,
                    bet_type=bet.bet_type,
                    number=bet.number,
                    status=bet.status,
                ))

        return total_bets

    def roll_dice(self) -> tuple[int, int]:
        if not (self.dice and self.stats and self.table and self.play_by_play and self.roll_history_manager and self.game_state and self.player_lineup):
            raise RuntimeError("SessionManager missing required components for rolling dice.")

        shooter_name = self.game_state.shooter.name if self.game_state.shooter else f"Shooter {self.shooter_index + 1}"
        roll_num = self.stats.session_rolls + 1  # next roll

        outcome = self.dice.roll()
        total = sum(outcome)

        self.events.publish(DiceRolled(
            shooter_index=self.shooter_index,
            roll_number=roll_num,
            dice=outcome,
            total=total,
            phase=self.game_state.phase,
            point=self.game_state.point,
            table_risk=self.table.total_risk(),
            shooter_name=shooter_name,
        ))

        return outcome

    def resolve_bets(self, outcome: tuple[int, int]) -> None:
        if not (self.table and self.game_state and self.stats and self.play_by_play and self.house_rules):
            raise RuntimeError("Missing components for resolving bets.")

        # Step 0: Update ATS tracking
        total = sum(outcome)
        if total != 7:
            ats_message = self.game_state.record_number_hit(total)
            if ats_message:
                self.events.publish(NumberHit(total=total, message=ats_message))
        
        # Snapshot number-fill candidates so travel is observable after
        # settlement (the mutation itself happens deep in resolution).
        unfilled_numbers = {
            id(bet)
            for bet in self.table.bets
            if bet.bet_type in _NUMBER_FILL_BET_TYPES and bet.number is None
        }

        # Step 1: Check active bets
        self.table.check_bets(outcome, self.game_state)

        # Step 2: Settle resolved bets
        resolved_bets = self.table.settle_resolved_bets()

        # Step 2b: Publish bets that acquired their number and stayed up
        # (Come/Don't Come travel, odds attaching to the point).
        for bet in self.table.bets:
            if id(bet) in unfilled_numbers and isinstance(bet.number, int):
                self.events.publish(BetMoved(
                    player_name=bet.owner.name,
                    bet_type=bet.bet_type,
                    amount=bet.amount,
                    number=bet.number,
                ))

        # Step 3: Publish resolutions (stats consumer keeps the ledger)
        for bet in resolved_bets:
            self.events.publish(BetResolved(
                player_name=bet.owner.name,
                bet_type=bet.bet_type,
                amount=bet.amount,
                number=bet.number,
                status=bet.status,
                payout=bet.resolved_payout,
                win_payout=bet.payout(),
                removed=not any(b is bet for b in self.table.bets),
            ))

            # Step 4: Notify strategy if bet won
            if bet.status == "won":
                payout = bet.resolved_payout
                strategy = getattr(bet.owner, "betting_strategy", None)
                if strategy and hasattr(strategy, "notify_payout"):
                    strategy.notify_payout(payout)

        # Step 5: Update game state
        state_message = self.game_state.update_state(outcome)
        self.events.publish(GameStateChanged(message=state_message))

        # Step 6: Adjust strategy bets
        self.adjust_bets()

    def adjust_bets(self) -> None:
        """Let each strategy adjust bets after resolution (before next roll)."""
        if not self.game_state or not self.player_lineup or not self.table:
            raise RuntimeError("Missing game components for adjusting bets.")

        players = self.player_lineup.get_active_players_list()
        for player in players:
            strategy = getattr(player, "betting_strategy", None)
            if strategy and hasattr(strategy, "adjust_bets"):
                changed = strategy.adjust_bets(self.game_state, player, self.table)
                for bet in changed or ():
                    self.events.publish(BetAdjusted(
                        player_name=bet.owner.name,
                        bet_type=bet.bet_type,
                        amount=bet.amount,
                        number=bet.number,
                        status=bet.status,
                    ))

        if self.stats:
            self.events.publish(BankrollsUpdated(
                bankrolls=tuple((p.name, p.balance) for p in players),
            ))

    def assign_next_shooter(self) -> None:
        if not self.game_state or not self.player_lineup:
            return

        players = self.player_lineup.get_active_players_list()
        if not players:
            return
        
        # 💥 Avoid assigning more shooters than we have planned
        if not self.stats or self.shooter_index >= self.stats.num_shooters:
            return  # Reached max shooters, do not assign more

        # Save starting bankrolls for each player at the start of a new shooter
        if self.stats and self.player_lineup:
            snapshot = {
                player.name: player.balance
                for player in self.player_lineup.get_active_players_list()
            }
            self._starting_bankroll_snapshot = snapshot  # cache for comparison

        self.shooter_index += 1
        shooter = players[(self.shooter_index - 1) % len(players)]  # Use previous index for assignment
        self.game_state.assign_new_shooter(shooter, self.shooter_index)
        self.events.publish(ShooterAssigned(
            shooter_index=self.shooter_index,
            shooter_name=shooter.name,
        ))

    def refresh_bet_statuses(self) -> None:
        """Reset bet statuses based on game phase, house rules, and strategy preferences."""
        if not self.table or not self.game_state or not self.house_rules:
            return

        statuses_before = [(bet, bet.status) for bet in self.table.bets]

        for bet in self.table.bets:
            strategy = getattr(bet.owner, "betting_strategy", None)
            is_turned_off = getattr(strategy, "turned_off", False)

            if bet.bet_type == "Field":
                bet.status = "active"

            elif bet.bet_type in ["Place", "Buy", "Lay", "Don't Place"]:
                if (self.game_state.phase == "point" or self.house_rules.leave_bets_working) and not is_turned_off:
                    bet.status = "active"
                else:
                    bet.status = "inactive"

            elif bet.bet_type in ["Hop", "Proposition", "Hardways", "Any Craps"]:
                if bet.status == "won":
                    bet.status = "active"

        for bet, old_status in statuses_before:
            if bet.status != old_status:
                self.events.publish(BetStatusChanged(
                    player_name=bet.owner.name,
                    bet_type=bet.bet_type,
                    number=bet.number,
                    status=bet.status,
                ))

        if self.stats and self.player_lineup:
            self.events.publish(RiskUpdated(at_risk=tuple(
                (
                    player.name,
                    sum(b.amount for b in self.table.bets if b.owner == player and b.status == "active"),
                )
                for player in self.player_lineup.get_active_players_list()
            )))

    def handle_post_roll(self, outcome: tuple[int, int], previous_phase: str) -> PostRollSummary:
        if not self.game_state or not self.stats:
            raise RuntimeError("Game state or statistics not initialized.")
        
        if not self.player_lineup:
            raise RuntimeError("PlayerLineup is not initialized.")

        total = sum(outcome)
        current_phase = self.game_state.phase
        puck_on = self.game_state.puck_on

        # Detect 7-out since phase has changed
        seven_out = previous_phase == "point" and total == 7

        point_was_hit = (
            previous_phase == "point"
            and current_phase == "come-out"
            and total == self.game_state.previous_point
        )
        transitioned = previous_phase != current_phase
        new_shooter_assigned = False

        if previous_phase == "come-out" and current_phase == "point" and self.game_state.point is not None:
            self.events.publish(PointEstablished(point=self.game_state.point))
        if point_was_hit and self.game_state.previous_point is not None:
            self.events.publish(PointHit(point=self.game_state.previous_point))

        if seven_out:
            # Compute shooter results for the event (stats consumer records them)
            shooter_results: tuple[tuple[str, int], ...] = ()
            if self.stats and self.player_lineup and hasattr(self, "_starting_bankroll_snapshot"):
                ending_snapshot = {
                    player.name: player.balance
                    for player in self.player_lineup.get_active_players_list()
                }
                shooter_results = tuple(
                    (name, ending_snapshot[name] - starting_balance)
                    for name, starting_balance in self._starting_bankroll_snapshot.items()
                )
                del self._starting_bankroll_snapshot  # clean up

            self.events.publish(SevenOut(
                shooter_index=self.shooter_index,
                shooter_results=shooter_results,
            ))
            self.game_state.clear_shooter()
            for player in self.player_lineup.get_active_players_list():
                strategy = getattr(player, "betting_strategy", None)
                if strategy and hasattr(strategy, "on_new_shooter"):
                    strategy.on_new_shooter()
            self.assign_next_shooter()
            new_shooter_assigned = True

        # ✅ Shooter continues if it’s a come-out roll and not a 7-out
        shooter_continues = not seven_out and current_phase == "come-out"

        return PostRollSummary(
            total=total,
            seven_out=seven_out,
            point_was_hit=point_was_hit,
            transitioned=transitioned,
            puck_on=puck_on,
            new_shooter_assigned=new_shooter_assigned,
            shooter_continues=shooter_continues,
        )
    
    def finalize_session(self,
        stats: Statistics,
        dice_mode: str,
        roll_history: list[dict[str, Any]],
        roll_history_manager: RollHistoryManager,
        play_by_play: PlayByPlay,
        players: list[Any]
    ) -> Statistics:
        
        # Save roll history if running in live mode
        if dice_mode == "live" and not self.quiet_mode:
            roll_history_manager.save_roll_history(roll_history)

        # View the play-by-play log
        if not self.quiet_mode:
            log_viewer = InteractiveLogViewer()
            log_viewer.view(play_by_play.play_by_play_file)

        # ✅ Save the stats
        stats.roll_history = roll_history
        stats.update_player_stats(players)
        
        # Track session high/low roller after final bankrolls are known
        best = None
        worst = None
        for player in players:
            strategy = getattr(player.betting_strategy, "strategy_name", "Unknown")
            start = stats.player_stats[player.name]["initial_bankroll"]
            final = stats.player_stats[player.name]["final_bankroll"]
            profit = final - start

            if best is None or profit > best[2]:
                best = (player.name, strategy, profit)
            if worst is None or profit < worst[2]:
                worst = (player.name, strategy, profit)

        stats.session_high_roller = best
        stats.session_low_roller = worst

        self.events.publish(SessionFinalized(session_rolls=stats.session_rolls))
        
        # Build the report, and display the statistics
        if not self.quiet_mode:
            self.report_writer.write_statistics(stats)
            log_viewer.view("output/statistics_report.txt")

        # Visualize player bankrolls (only if there are players and rolls)
        if self.quiet_mode:
            visualizer_path = "output/session_visualizer.png"
            if os.path.exists(visualizer_path):
                os.remove(visualizer_path)
        else:
            if stats.num_players == 0 or stats.session_rolls == 0:
                print("⚠️ No data to visualize — skipping charts.")
            else:
                self.visualizer.visualize_bankrolls()
        
        return stats

    def log_player_bets(self) -> None:
        if not self.player_lineup or not self.table or not self.play_by_play:
            return

        for player in self.player_lineup.get_active_players_list():
            remaining_bets = [b for b in self.table.bets if b.owner == player]
            if remaining_bets:
                summary = ", ".join(
                    f"{b.bet_type} {b.number} (${b.amount} {b.status})" if b.number is not None else f"{b.bet_type} (${b.amount} {b.status})"
                    for b in remaining_bets
                )
                bet_total = sum(b.amount for b in remaining_bets)
                self.play_by_play.write(
                    f"  📊 {player.name}'s remaining bets: {summary} | Total on table: ${bet_total} Bankroll: ${player.balance}"
                )
