# File: craps/bets/place_odds.py
from . import Bet

class PlaceOddsBet(Bet):
    """Class representing a Place Odds bet."""
    def __init__(self, amount, owner, number):
        """
        Initialize a Place Odds bet.
        
        :param amount: The amount of the bet.
        :param owner: The player who placed the bet.
        :param number: The number being bet on (e.g., 4, 5, 6, 8, 9, 10).
        """
        super().__init__(f"Place Odds on {number}", amount, owner, payout_ratio=(1, 1), locked=False)
        self.number = number

    def resolve(self, outcome, phase, point):
        """Resolve the Place Odds bet based on the dice outcome, phase, and point."""
        total = sum(outcome)
        
        if phase == "point":
            if total == self.number:
                # Set the payout ratio based on the number
                if self.number in [4, 10]:
                    self.payout_ratio = (2, 1)  # 2:1 payout for 4 and 10
                elif self.number in [5, 9]:
                    self.payout_ratio = (3, 2)  # 3:2 payout for 5 and 9
                elif self.number in [6, 8]:
                    self.payout_ratio = (6, 5)  # 6:5 payout for 6 and 8
                self.status = "won"  # Place Odds bet wins
            elif total == 7:
                self.status = "lost"  # Place Odds bet loses
            else:
                self.status = "active"  # Bet remains active