# File: craps/bet.py

from typing import List, Optional, Tuple

class Bet:
    """Base class for all bet types."""
    def __init__(self, bet_type: str, amount: int, owner: str, payout_ratio: Tuple[int, int] = (1, 1), locked: bool = True, vig: int = 0):
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

    def resolve(self, dice_outcome: List[int], phase: str, point: Optional[int]) -> None:
        """
        Resolve the bet based on the dice outcome, phase, and point.

        :param dice_outcome: The result of the dice roll (e.g., [3, 4]).
        :param phase: The current game phase ("come-out" or "point").
        :param point: The current point number (if in point phase).
        """
        raise NotImplementedError("Subclasses must implement this method.")

    def is_resolved(self) -> bool:
        """Check if the bet has been resolved (won, lost, or pushed)."""
        return self.status in ["won", "lost", "pushed"]

    def payout(self) -> int:
        """
        Calculate the payout for the bet.

        :return: The payout amount.
        """
        if self.status != "won":
            return 0

        numerator, denominator = self.payout_ratio
        profit = self.amount * numerator // denominator

        # Deduct the vig (if applicable)
        if self.vig > 0:
            vig_amount = self.amount * self.vig // 100
            profit -= vig_amount

        return profit if self.bet_type != "Pass Line" else self.amount + profit

    def __str__(self):
        return f"{self.owner}'s ${self.amount} {self.bet_type} bet (Status: {self.status})"