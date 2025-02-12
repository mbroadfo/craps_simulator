# File: .\craps\bets\pass_line.py

from . import Bet  # Import the base Bet class from the bets package

class PassLineBet(Bet):
    """Class representing a Pass Line bet."""
    def __init__(self, amount, owner):
        super().__init__("Pass Line", amount, owner, payout_ratio=(1, 1), locked=True)

    def resolve(self, outcome, phase, point):
        """Resolve the Pass Line bet based on the dice outcome, phase, and point."""
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