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
            self.dice = Dice()

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

        self.initialized = True
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

        self.play_by_play.write("  ---------- Place Your Bets! -------------")
        total_bets = 0

        for player in self.player_lineup.get_active_players_list():
            if not player.betting_strategy:
                continue

            bets = player.betting_strategy.place_bets(
                game_state=self.game_state,
                player=player,
                table=self.table
            )

            if bets:
                success = player.place_bet(
                    bets,
                    table=self.table,
                    phase=self.game_state.phase,
                    play_by_play=self.play_by_play
                )
                if success:
                    total_bets += len(bets) if isinstance(bets, list) else 1

        return total_bets

    def roll_dice(self) -> tuple[int, int]:
        if not (self.dice and self.stats and self.table and self.play_by_play and self.roll_history_manager and self.game_state and self.player_lineup):
            raise RuntimeError("SessionManager missing required components for rolling dice.")

        # 📣 Visual separator with shooter context
        shooter_name = self.game_state.shooter.name if self.game_state.shooter else f"Shooter {self.shooter_index + 1}"
        roll_num = self.stats.session_rolls + 1  # next roll
        self.play_by_play.write(f"  ---------- Shooter {self.shooter_index} ({shooter_name}) — Roll #{roll_num} ----------")

        outcome = self.dice.roll()
        total = sum(outcome)

        players = self.player_lineup.get_active_players_list()
        shooter = players[self.shooter_index % len(players)]
        self.stats.update_rolls(total=total, table_risk=self.table.total_risk())
        self.stats.update_shooter_stats(shooter)

        puck_state = ("Puck OFF" if self.game_state.phase == "come-out" else f"Puck ON {self.game_state.point}")
        roll_message = f"  🎲 Roll #{self.stats.session_rolls} → {outcome} = {total} ({puck_state})"
        self.play_by_play.write(roll_message)

        self.roll_history.append({
            "shooter_num": self.shooter_index + 1,
            "roll_number": self.stats.session_rolls,
            "dice": list(outcome),
            "total": total,
            "phase": self.game_state.phase,
            "point": self.game_state.point
        })

        return outcome

    def resolve_bets(self, outcome: tuple[int, int]) -> None:
        if not (self.table and self.game_state and self.stats and self.play_by_play and self.house_rules):
            raise RuntimeError("Missing components for resolving bets.")

        # Step 0: Update ATS tracking
        if self.game_state.phase == "point" and sum(outcome) != 7:
            ats_message = self.game_state.record_number_hit(sum(outcome))
            if ats_message:
                self.play_by_play.write(ats_message)
        
        # Step 1: Check active bets
        self.table.check_bets(outcome, self.game_state)

        # Step 2: Settle resolved bets
        resolved_bets = self.table.settle_resolved_bets()

        # Step 3: Update win/loss stats
        for bet in resolved_bets:
            self.stats.update_win_loss(bet)

            # Step 4: Notify strategy if bet won
            if bet.status == "won":
                payout = bet.resolved_payout
                strategy = getattr(bet.owner, "betting_strategy", None)
                if strategy and hasattr(strategy, "notify_payout"):
                    strategy.notify_payout(payout)

        # Step 5: Remove winning bets based on house rules
        for bet in resolved_bets:
            if bet.status == "won" and bet in self.table.bets:
                if bet.is_contract_bet or not self.house_rules.leave_winning_bets_up:
                    self.table.bets.remove(bet)
        
        # Step 6: Update game state
        state_message = self.game_state.update_state(outcome)
        self.play_by_play.write(state_message)

        # Step 7: Adjust strategy bets
        self.adjust_bets()

    def adjust_bets(self) -> None:
        """Let each strategy adjust bets after resolution (before next roll)."""
        if not self.game_state or not self.player_lineup or not self.table:
            raise RuntimeError("Missing game components for adjusting bets.")

        for player in self.player_lineup.get_active_players_list():
            strategy = getattr(player, "betting_strategy", None)
            if strategy and hasattr(strategy, "adjust_bets"):
                strategy.adjust_bets(self.game_state, player, self.table)
        
        if self.stats:
            self.stats.update_player_bankrolls(self.player_lineup.get_active_players_list())

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

    def refresh_bet_statuses(self) -> None:
        """Reset bet statuses based on game phase, house rules, and strategy preferences."""
        if not self.table or not self.game_state or not self.house_rules:
            return

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

            elif bet.bet_type in ["Hop", "Proposition", "Hardways"]:
                if bet.status == "won":
                    bet.status = "active"
                    
        if self.stats and self.player_lineup:
            self.stats.update_player_risk(
                self.player_lineup.get_active_players_list(),
                self.table
            )

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
        
        if seven_out:
            # Record shooter results into statistics
            if self.stats and self.player_lineup and hasattr(self, "_starting_bankroll_snapshot"):
                ending_snapshot = {
                    player.name: player.balance
                    for player in self.player_lineup.get_active_players_list()
                }
                result = {
                    name: ending_snapshot[name] - starting_balance
                    for name, starting_balance in self._starting_bankroll_snapshot.items()
                }
                self.stats.shooter_stats[self.shooter_index] = result
                del self._starting_bankroll_snapshot  # clean up

            self.stats.record_seven_out()
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
                    f"{b.bet_type} {b.number} (${b.amount} {b.status})" for b in remaining_bets
                )
                bet_total = sum(b.amount for b in remaining_bets)
                self.play_by_play.write(
                    f"  📊 {player.name}'s remaining bets: {summary} | Total on table: ${bet_total} Bankroll: ${player.balance}"
                )
