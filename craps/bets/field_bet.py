# File: .\craps\bets\field_bet.py

from . import Bet  # Import the base Bet class

class FieldBet(Bet):
    """Class representing a Field bet."""
    def __init__(self, amount, owner):
        super().__init__("Field", amount, owner, payout_ratio=(1, 1), locked=False)

    def resolve(self, outcome, phase, point):
        """Resolve the Field bet based on the dice outcome."""
        if phase not in self.valid_phases:
            return  # Do not resolve the bet if the phase is invalid

        total = sum(outcome)

        # Field bet wins on 2, 3, 4, 9, 10, 11, 12
        if total in [2, 3, 4, 9, 10, 11, 12]:
            if total in [2, 12]:  # Special payouts for 2 and 12
                self.payout_ratio = (2, 1)  # 2:1 payout for 2 and 12 (adjust as needed)
            self.status = "won"  # Field bet wins
        else:
            self.status = "lost"  # Field bet loses
            
    def payout(self) -> int:
        """
        Calculate the payout for the Field bet.
        """
        if self.status != "won":
            return 0

        # Pass Line bets pay 1:1
        numerator, denominator = self.payout_ratio
        return self.amount + (self.amount * numerator // denominator)
