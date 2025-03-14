from typing import Dict, Tuple, Optional
from craps.house_rules import HouseRules
from craps.table import Table
from craps.roll_history_manager import RollHistoryManager
from craps.log_manager import LogManager
from craps.play_by_play import PlayByPlay
from craps.rules_engine import RulesEngine

class InitializeSession:
    def __init__(self, session_mode: str, house_rules_config: Dict[str, int]) -> None:
        """
        Initialize the session.

        :param session_mode: The session mode ("live" or "history").
        :param house_rules_config: The house rules configuration.
        """
        self.session_mode: str = session_mode
        self.house_rules_config: Dict[str, int] = house_rules_config
        self.roll_history_manager: RollHistoryManager = RollHistoryManager()
        self.log_manager: LogManager = LogManager()
        self.play_by_play: PlayByPlay = PlayByPlay()
        self.rules_engine: RulesEngine = RulesEngine()

    def prepare_session(self) -> Optional[Tuple[HouseRules, Table, RollHistoryManager, LogManager, PlayByPlay]]:
        """Prepare the session based on the session mode."""
        try:
            self.roll_history_manager.prepare_for_session(self.session_mode)
        except (ValueError, FileNotFoundError) as e:
            print(f"Error: {e}")
            return None

        # Initialize house rules
        house_rules = HouseRules(self.house_rules_config)

        # Create the Table object with the RulesEngine
        table = Table(house_rules, self.play_by_play)

        # Delete the existing log file before starting the session
        self.log_manager.delete_log_file()

        # Clear the play-by-play file before starting the session
        self.play_by_play.clear_play_by_play_file()

        return house_rules, table, self.roll_history_manager, self.log_manager, self.play_by_play
