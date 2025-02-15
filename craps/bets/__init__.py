# File: .\craps\bets\__init__.py

# Define the base Bet class
class Bet:
    """Base class for all bet types."""
    def __init__(self, bet_type, amount, owner, payout_ratio=(1, 1), locked=True, vig=0):
        """
        Initialize a bet.
        
        :param bet_type: The type of bet (e.g., "Pass Line", "Come").
        :param amount: The amount of the bet.
        :param owner: The player who placed the bet.
        :param payout_ratio: The payout ratio as a tuple (numerator, denominator).
        :param locked: Whether the bet is locked (cannot be taken down).
        :param vig: The vig (commission) as a percentage of the bet amount.
        """
        self.bet_type = bet_type
        self.amount = amount
        self.owner = owner
        self.payout_ratio = payout_ratio
        self.locked = locked
        self.vig = vig
        self.status = "active"  # Can be "active", "won", "lost", or "pushed"

    def calculate_profit(self):
        """Calculate the profit for the bet based on the payout ratio and vig."""
        numerator, denominator = self.payout_ratio
        profit = self.amount * numerator // denominator
        
        # Deduct the vig (if applicable)
        if self.vig > 0:
            vig_amount = self.amount * self.vig // 100
            profit -= vig_amount
        
        return profit

    def payout(self):
        """
        Calculate the payout for the bet.
        - For Pass-Line bets: Return the total payout (original bet + profit).
        - For Place bets: Return the profit only (original bet remains on the table).
        """
        if self.status != "won":
            return 0  # No payout if the bet is not won
        
        profit = self.calculate_profit()
        
        # Return the total payout for Pass-Line bets or profit only for Place bets
        if self.bet_type == "Pass Line":
            return self.amount + profit  # Total payout (original bet + profit)
        else:
            return profit  # Profit only (original bet remains on the table)

    def resolve(self, outcome, phase, point):
        """
        Resolve the bet based on the dice outcome, phase, and point.
        
        :param outcome: The result of the dice roll (e.g., [3, 4]).
        :param phase: The current game phase ("come-out" or "point").
        :param point: The current point number (if in point phase).
        """
        raise NotImplementedError("Subclasses must implement this method.")

    def is_resolved(self):
        """Check if the bet has been resolved (won, lost, or pushed)."""
        return self.status in ["won", "lost", "pushed"]

    def __str__(self):
        return f"{self.owner}'s ${self.amount} {self.bet_type} bet (Status: {self.status})"


# Import and re-export the bet classes
from .pass_line import PassLineBet
from .place_bet import PlaceBet
from .free_odds import FreeOddsBet

# Optionally, define __all__ to make it clear which classes are exported
__all__ = ["Bet", "PassLineBet", "PlaceBet", "PassLineOddsBet"]