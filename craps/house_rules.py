# File: craps/house_rules.py
class HouseRules:
    """Class representing house rules for payouts and table limits."""
    def __init__(self):
        # Default payout ratios for Field Bet
        self.field_bet_payout_2 = (2, 1)  # 2:1 payout for 2
        self.field_bet_payout_12 = (3, 1)  # 3:1 payout for 12

        # Table limits
        self.table_minimum = 10  # Minimum bet amount
        self.table_maximum = 5000  # Maximum bet amount

    def set_field_bet_payouts(self, payout_2, payout_12):
        """Set the payout ratios for the Field Bet."""
        self.field_bet_payout_2 = payout_2
        self.field_bet_payout_12 = payout_12

    def set_table_limits(self, minimum, maximum):
        """Set the table limits."""
        self.table_minimum = minimum
        self.table_maximum = maximum