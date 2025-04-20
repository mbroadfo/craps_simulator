from typing import Tuple, Optional
from craps.house_rules import HouseRules
from craps.table import Table
from craps.roll_history_manager import RollHistoryManager
from craps.log_manager import LogManager
from craps.play_by_play import PlayByPlay
from craps.rules_engine import RulesEngine
from craps.statistics import Statistics
from craps.game_state import GameState
from craps.lineup import PlayerLineup
from craps.statistics_report import StatisticsReport
class InitializeSession:
    def __init__(
        self, 
        dice_mode: str, 
        house_rules: HouseRules,
        play_by_play: PlayByPlay, 
        rules_engine: RulesEngine, 
        player_lineup: PlayerLineup,
        log_manager: Optional[LogManager] = None
    ) -> None:
        """
        Initialize the session.

        :param dice_mode: The session mode ("live" or "history").
        :param house_rules: The HouseRules instance of the session.
        :param play_by_play: The PlayByPlay instance for logging session messages.
        :param rules_engine: The RulesEngine instance to use for the session.
        :param log_manager: The LogManager instance for managing session logs.
        """
        self.dice_mode: str = dice_mode
        self.house_rules: HouseRules = house_rules
        self.roll_history_manager: RollHistoryManager = RollHistoryManager()
        self.log_manager = log_manager or LogManager()
        self.play_by_play: PlayByPlay = play_by_play
        self.rules_engine: RulesEngine = rules_engine
        self.player_lineup: PlayerLineup = player_lineup

    def prepare_session(
        self, num_shooters: int, num_players: int
    ) -> Optional[Tuple[HouseRules, Table, RollHistoryManager, LogManager, PlayByPlay, Statistics, GameState]]:
        """Prepare the session based on the session mode."""
        try:
            self.roll_history_manager.prepare_for_session(self.dice_mode)
        except (ValueError, FileNotFoundError) as e:
            print(f"Error: {e}")
            return None

        table = Table(self.house_rules, self.play_by_play, self.rules_engine, self.player_lineup)

        # Initialize Statistics and GameState
        stats = Statistics(self.house_rules.table_minimum, num_shooters, num_players)
        game_state = GameState(stats, play_by_play=self.play_by_play)
        game_state.set_table(table)
        table.set_game_state(game_state)

        # Delete the existing log file before starting the session
        self.log_manager.delete_log_file()

        # Clear the play-by-play file before starting the session
        self.play_by_play.clear_play_by_play_file()

        # Clear the Statistics Report before starting the session        
        StatisticsReport().clear_statistics_file()

        return self.house_rules, table, self.roll_history_manager, self.log_manager, self.play_by_play, stats, game_state
