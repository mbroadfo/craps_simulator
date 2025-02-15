# File: craps/bets/field_bet.py
from . import Bet  # Import the base Bet class

class FieldBet(Bet):
    """Class representing a Field bet."""
    def __init__(self, amount, owner):
        super().__init__("Field", amount, owner, payout_ratio=(1, 1), locked=False)

    def resolve(self, outcome, phase, point):
        """Resolve the Field bet based on the dice outcome."""
        total = sum(outcome)

        # Field bet wins on 2, 3, 4, 9, 10, 11, 12
        if total in [2, 3, 4, 9, 10, 11, 12]:
            if total in [2, 12]:  # Special payouts for 2 and 12
                self.payout_ratio = (2, 1)  # 2:1 payout for 2 and 12 (adjust as needed)
            self.status = "won"  # Field bet wins
        else:
            self.status = "lost"  # Field bet loses