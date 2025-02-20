# File: .\craps\initialize_session.py

from craps.house_rules import HouseRules
from craps.table import Table
from craps.roll_history_manager import RollHistoryManager

class InitializeSession:
    def __init__(self, session_mode, house_rules_config):
        self.session_mode = session_mode
        self.house_rules_config = house_rules_config
        self.roll_history_manager = RollHistoryManager()

    def prepare_session(self):
        """Prepare the session based on the session mode."""
        try:
            self.roll_history_manager.prepare_for_session(self.session_mode)
        except (ValueError, FileNotFoundError) as e:
            print(f"Error: {e}")
            return None

        # Initialize house rules
        house_rules = HouseRules(self.house_rules_config)

        # Create the Table object
        table = Table(house_rules)

        return house_rules, table, self.roll_history_manager