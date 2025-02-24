# File: .\craps\bets\place_bet.py

from . import Bet  # Import the base Bet class from the bets package

class PlaceBet(Bet):
    """Class representing a Place bet."""
    def __init__(self, amount, owner, number):
        """
        Initialize a Place bet.

        :param amount: The amount of the bet.
        :param owner: The player who placed the bet.
        :param number: The number associated with the bet (e.g., 6 for Place 6).
        """
        super().__init__(
            bet_type="Place",
            amount=amount,
            owner=owner,
            locked=False,
            valid_phases=["point"],  # Place bets are only valid during the point phase
            number=number  # Number associated with the bet (e.g., 6 for Place 6)
        )

    def resolve(self, outcome, phase, point):
        """Resolve the Place bet based on the dice outcome, phase, and point."""
        if phase not in self.valid_phases:
            return  # Do not resolve the bet if the phase is invalid

        total = sum(outcome)
        
        if phase == "come-out":
            self.status = "inactive"  # Place bets are inactive during the come-out phase
            return
        
        if phase == "point":
            if total == self.number:
                if self.number in [4, 10]:
                    self.payout_ratio = (9, 5)  # 9:5 payout for 4 and 10
                elif self.number in [5, 9]:
                    self.payout_ratio = (7, 5)  # 7:5 payout for 5 and 9
                elif self.number in [6, 8]:
                    self.payout_ratio = (7, 6)  # 7:6 payout for 6 and 8
                self.status = "won"  # Place bet wins
            elif total == 7:
                self.status = "lost"  # Place bet loses on 7-out
            else:
                self.status = "active"  # Bet remains active

    def payout(self) -> int:
        """
        Calculate the payout for the Place bet.
        """
        if self.status != "won":
            return 0

        numerator, denominator = self.payout_ratio
        profit = (self.amount * numerator) // denominator  # Calculate profit
        return self.amount + profit  # Return total payout (original bet + profit)