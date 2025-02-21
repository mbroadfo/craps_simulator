# File: .\craps\bets\pass_line.py

from craps.bet import Bet  # Import the base Bet class from craps.bet

class PassLineBet(Bet):
    """Class representing a Pass Line bet."""
    def __init__(self, amount, owner):
        super().__init__(
            bet_type="Pass Line",
            amount=amount,
            owner=owner,
            payout_ratio=(1, 1),
            locked=True,
            valid_phases=["come-out"]  # Pass Line bets are only valid during the come-out phase
        )

    def resolve(self, outcome, phase, point):
        """Resolve the Pass Line bet based on the dice outcome, phase, and point."""
        if phase not in self.valid_phases:
            return  # Do not resolve the bet if the phase is invalid

        total = sum(outcome)
        
        if phase == "come-out":
            if total in [7, 11]:
                self.status = "won"  # Pass Line bet wins
            elif total in [2, 3, 12]:
                self.status = "lost"  # Pass Line bet loses
            else:
                self.status = "active"  # Point is set; bet remains active
        else:  # Point phase
            if total == point:
                self.status = "won"  # Pass Line bet wins
            elif total == 7:
                self.status = "lost"  # Pass Line bet loses
            else:
                self.status = "active"  # Bet remains active
                
    def payout(self) -> int:
        """
        Calculate the payout for the Pass Line bet.
        """
        if self.status != "won":
            return 0

        # Pass Line bets pay 1:1
        numerator, denominator = self.payout_ratio
        return self.amount + (self.amount * numerator // denominator)