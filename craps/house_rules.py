from typing import Any

class HouseRules:
    """Class representing house rules for payouts and table limits."""

    def __init__(self, config: dict[str, Any]) -> None:
        """
        Initialize the HouseRules with configuration from config.py.

        :param config: A dictionary containing house rules configuration.
        """
        self.table_minimum: int = config.get("table_minimum", 10)  # Default to $10
        self.table_maximum: int = config.get("table_maximum", 5000)  # Default to $5000
        
        # ✅ Sessuib behavioral toggles from config
        self.come_odds_working_on_come_out: bool = config.get("come_odds_working_on_come_out", False)
        self.leave_bets_working: bool = config.get("leave_bets_working", False)
        self.leave_winning_bets_up: bool = config.get("leave_winning_bets_up", True)

    def set_table_limits(self, minimum: int, maximum: int) -> None:
        """Set the table limits."""
        self.table_minimum = minimum
        self.table_maximum = maximum
