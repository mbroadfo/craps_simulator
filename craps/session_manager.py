from __future__ import annotations
from typing import Optional, Any, NamedTuple
from config import HOUSE_RULES, ACTIVE_PLAYERS, DICE_TEST_PATTERNS
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


class SessionManager:
    def __init__(self) -> None:
        self.house_rules: Optional[HouseRules] = None
        self.table: Optional[Table] = None
        self.roll_history_manager: Optional[RollHistoryManager] = None
        self.log_manager: Optional[LogManager] = None
        self.play_by_play: Optional[PlayByPlay] = None
        self.rules_engine: Optional[RulesEngine] = None
        self.stats: Optional[Statistics] = None
        self.game_state: Optional[GameState] = None
        self.player_lineup: Optional[PlayerLineup] = None
        self.dice: Optional[Dice] = None
        self.initialized: bool = False
        self.locked: bool = False
        self.shooter_index: int = 0
        self.roll_history: list[dict[str, Any]] = []

    def setup_session(
        self,
        house_rules_dict: Optional[dict[str, Any]] = None,
        num_shooters: int = 10,
        num_players: int = 0,
        dice_mode: str = "live", # "live" or "history"
        roll_history_file: Optional[str] = None,
        pattern_name: Optional[str] = None
    ) -> bool:
        """
        Initializes core game components and prepares the session.
        """
        self.house_rules = HouseRules(house_rules_dict or HOUSE_RULES)
        self.play_by_play = PlayByPlay()
        self.log_manager = LogManager()
        self.rules_engine = RulesEngine()
        self.player_lineup = PlayerLineup(self.house_rules, None, self.play_by_play, self.rules_engine)

        # ✅ Initialize Dice
        if dice_mode == "history" and roll_history_file:
            self.dice = Dice(roll_history_file)
        else:
            self.dice = Dice()
            if dice_mode == "pattern" and pattern_name in DICE_TEST_PATTERNS:
                self.dice.forced_rolls.extend(DICE_TEST_PATTERNS[pattern_name])

        # ✅ Initialize Session
        session_initializer = InitializeSession(
            dice_mode=dice_mode,
            house_rules=self.house_rules,
            play_by_play=self.play_by_play,
            log_manager=self.log_manager,
            rules_engine=self.rules_engine,
            player_lineup=self.player_lineup
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

        roll_message = f"  🎲 Roll #{self.stats.session_rolls} → {outcome} = {total}"
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

        # Step 1: Check active bets
        self.table.check_bets(outcome, self.game_state.phase, self.game_state.point)

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

        # Step 7: Check for 7-out transition (must use updated phase!)
        if self.game_state.previous_point is not None and self.game_state.point is None and sum(outcome) == 7:
            self.stats.record_seven_out()
            self.game_state.clear_shooter()

            if not self.player_lineup:
                raise RuntimeError("SessionManager: player_lineup is not initialized.")

            for player in self.player_lineup.get_active_players_list():
                strategy = getattr(player, "betting_strategy", None)
                if strategy and hasattr(strategy, "on_new_shooter"):
                    strategy.on_new_shooter()

            self.assign_next_shooter()

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

        self.shooter_index += 1  # ✅ Increment first
        shooter = players[(self.shooter_index - 1) % len(players)]  # Use previous index for assignment
        self.game_state.assign_new_shooter(shooter, self.shooter_index)


    def refresh_bet_statuses(self) -> None:
        """Reset bet statuses based on game phase, house rules, and strategy preferences."""
        if not self.table or not self.game_state:
            return

        for bet in self.table.bets:
            strategy = getattr(bet.owner, "betting_strategy", None)
            is_turned_off = getattr(strategy, "turned_off", False)

            if bet.bet_type == "Field":
                bet.status = "active"
            elif bet.bet_type in ["Place", "Buy", "Lay"]:
                if self.house_rules and (self.game_state.phase == "point" or self.house_rules.leave_bets_working):
                    bet.status = "active"
                else:
                    bet.status = "inactive"
            elif bet.bet_type in ["Hop", "Hardways", "Proposition"]:
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

        seven_out = self.game_state.phase == "point" and sum(outcome) == 7
        point_was_hit = (
            previous_phase == "point"
            and current_phase == "come-out"
            and total == self.game_state.previous_point
        )
        transitioned = previous_phase != current_phase
        new_shooter_assigned = False

        if seven_out:
            self.stats.record_seven_out()
            self.game_state.clear_shooter()
            for player in self.player_lineup.get_active_players_list():
                strategy = getattr(player, "betting_strategy", None)
                if strategy and hasattr(strategy, "on_new_shooter"):
                    strategy.on_new_shooter()
            self.assign_next_shooter()
            new_shooter_assigned = True

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
        if dice_mode == "live":
            roll_history_manager.save_roll_history(roll_history)

        # View the play-by-play log
        log_viewer = InteractiveLogViewer()
        log_viewer.view(play_by_play.play_by_play_file)

        # ✅ Save the stats, build the report, and display the statistics
        stats.roll_history = roll_history
        stats.update_player_stats(players)
        statistics_report = StatisticsReport()
        statistics_report.write_statistics(stats)
        log_viewer.view("output/statistics_report.txt")

        # Visualize player bankrolls (only if there are players and rolls)
        if stats.num_players == 0 or stats.session_rolls == 0:
            print("⚠️ No data to visualize — skipping charts.")
        else:
            visualizer = Visualizer(stats)
            visualizer.visualize_bankrolls()

        return stats
