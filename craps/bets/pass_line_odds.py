# File: .\craps\bets\pass_line_odds.py

from craps.bets import Bet  # Import the base Bet class

class PassLineOddsBet(Bet):
    """Class representing a Pass Line Odds bet."""
    def __init__(self, amount, owner):
        super().__init__("Pass Line Odds", amount, owner, payout_ratio=(1, 1), locked=False)

    def resolve(self, outcome, phase, point):
        """Resolve the Pass Line Odds bet based on the dice outcome, phase, and point."""
        total = sum(outcome)
        
        if phase == "point":
            if total == point:
                # Determine the payout ratio based on the point
                if point in [4, 10]:
                    self.payout_ratio = (2, 1)  # 2:1 payout for 4 and 10
                elif point in [5, 9]:
                    self.payout_ratio = (3, 2)  # 3:2 payout for 5 and 9
                elif point in [6, 8]:
                    self.payout_ratio = (6, 5)  # 6:5 payout for 6 and 8
                self.status = "won"  # Pass Line Odds bet wins
            elif total == 7:
                self.status = "lost"  # Pass Line Odds bet loses
            else:
                # Bet remains active
                self.status = "active"