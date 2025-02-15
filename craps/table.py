# File: craps/table.py
class Table:
    def __init__(self, house_rules):
        """
        Initialize the table.
        
        :param house_rules: The HouseRules object for payout rules and limits.
        """
        self.house_rules = house_rules
        self.bets = []
        self.unit = self.house_rules.table_minimum // 5

    def place_bet(self, bet):
        """Place a bet on the table."""
        if bet.amount < self.house_rules.table_minimum:
            raise ValueError(f"Bet amount ${bet.amount} is below the table minimum of ${self.house_rules.table_minimum}.")
        if bet.amount > self.house_rules.table_maximum:
            raise ValueError(f"Bet amount ${bet.amount} exceeds the table maximum of ${self.house_rules.table_maximum}.")
        self.bets.append(bet)

    def check_bets(self, outcome, phase, point):
        """Check and resolve all bets on the table based on the dice outcome, phase, and point."""
        for bet in self.bets:
            bet.resolve(outcome, phase, point)

    def get_minimum_bet(self, number):
        """
        Get the minimum bet for a Place bet on a specific number.
        
        :param number: The number being bet on (4, 5, 6, 8, 9, or 10).
        :return: The minimum bet amount.
        """
        if number in [6, 8]:
            # For 6 and 8, the minimum bet is table minimum + unit
            return self.house_rules.table_minimum + self.unit
        else:
            # For other numbers, the minimum bet is the table minimum
            return self.house_rules.table_minimum