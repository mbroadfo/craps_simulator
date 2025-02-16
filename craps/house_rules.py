# File: craps/house_rules.py

class HouseRules:
    """Class representing house rules for payouts and table limits."""
    def __init__(self, config):
        """
        Initialize the HouseRules with configuration from config.py.
        
        :param config: A dictionary containing house rules configuration.
        """
        self.field_bet_payout_2 = config.get("field_bet_payout_2", (2, 1))  # Default to 2:1 for 2
        self.field_bet_payout_12 = config.get("field_bet_payout_12", (3, 1))  # Default to 3:1 for 12
        self.table_minimum = config.get("table_minimum", 10)  # Default to $10
        self.table_maximum = config.get("table_maximum", 5000)  # Default to $5000

    def set_field_bet_payouts(self, payout_2, payout_12):
        """Set the payout ratios for the Field Bet."""
        self.field_bet_payout_2 = payout_2
        self.field_bet_payout_12 = payout_12

    def set_table_limits(self, minimum, maximum):
        """Set the table limits."""
        self.table_minimum = minimum
        self.table_maximum = maximum