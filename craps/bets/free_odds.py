# File: craps/bets/free_odds.py

from . import Bet

class FreeOddsBet(Bet):
    """Class representing a Free Odds bet (for Pass Line Odds or Place Bets)."""
    def __init__(self, bet_type, amount, owner, number=None):
        """
        Initialize a Free Odds bet.
        
        :param bet_type: The type of bet (e.g., "Pass Line Odds", "Place Odds").
        :param amount: The amount of the bet.
        :param owner: The player who placed the bet.
        :param number: The number being bet on (for Place Odds).
        """
        super().__init__(bet_type, amount, owner, payout_ratio=(1, 1), locked=False)
        self.number = number  # Only used for Place Odds

    def resolve(self, outcome, phase, point):
        """Resolve the Free Odds bet based on the dice outcome, phase, and point."""
        total = sum(outcome)
        
        if phase == "point":
            if self.bet_type == "Pass Line Odds":
                # Pass Line Odds logic
                if total == point:
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
                    self.status = "active"  # Bet remains active
            elif self.bet_type == "Place Odds":
                # Place Odds logic
                if total == self.number:
                    if self.number in [4, 10]:
                        self.payout_ratio = (2, 1)  # 2:1 payout for 4 and 10
                    elif self.number in [5, 9]:
                        self.payout_ratio = (3, 2)  # 3:2 payout for 5 and 9
                    elif self.number in [6, 8]:
                        self.payout_ratio = (7, 6)  # 7:6 payout for 6 and 8
                    self.status = "won"  # Place Odds bet wins
                elif total == 7:
                    self.status = "lost"  # Place Odds bet loses
                else:
                    self.status = "active"  # Bet remains active