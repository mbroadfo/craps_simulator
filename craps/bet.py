# File: .\craps\bet.py

from typing import List, Optional, Tuple
import logging

class Bet:
    """Base class for all bet types."""
    def __init__(
        self,
        bet_type: str,
        amount: int,
        owner,  # Reference to the Player object
        payout_ratio: Tuple[int, int] = (1, 1),
        locked: bool = True,
        vig: int = 0,
        unit: int = 1,  # Default unit for Place/Buy bets
        valid_phases: List[str] = ["come-out", "point"],  # Default valid phases
        come_point: Optional[int] = None,  # Point number for Come bets
    ):
        """
        Initialize a bet.

        :param bet_type: The type of bet (e.g., "Pass Line", "Come").
        :param amount: The amount of the bet.
        :param owner: The Player object who placed the bet.
        :param payout_ratio: The payout ratio as a tuple (numerator, denominator).
        :param locked: Whether the bet is locked (cannot be taken down).
        :param vig: The vig (commission) as a percentage of the bet amount.
        :param unit: The unit for Place/Buy bets (default is 1).
        :param valid_phases: The phases during which the bet can be placed (default is all phases).
        """
        self.bet_type = bet_type
        self.amount = amount
        self.owner = owner  # Store the Player object
        self.payout_ratio = payout_ratio
        self.locked = locked
        self.vig = vig
        self.unit = unit
        self.valid_phases = valid_phases
        self.status = "active"  # Can be "active", "won", "lost", or "pushed"
        self.come_point = come_point  # Point number for Come bets

    def validate_bet(self, phase: str, table_minimum: int, table_maximum: int) -> bool:
        """
        Validate the bet based on the game phase, table limits, and bet type.

        :param phase: The current game phase ("come-out" or "point").
        :param table_minimum: The table's minimum bet amount.
        :param table_maximum: The table's maximum bet amount.
        :return: True if the bet is valid, False otherwise.
        """
        # Check if the bet can be placed during the current phase
        if phase not in self.valid_phases:
            logging.warning(f"{self.owner.name}'s {self.bet_type} bet cannot be placed during the {phase} phase.")
            return False

        # Check if the bet amount is within table limits
        if self.amount < table_minimum:
            logging.warning(f"{self.owner.name}'s {self.bet_type} bet amount ${self.amount} is below the table minimum of ${table_minimum}.")
            return False
        if self.amount > table_maximum:
            logging.warning(f"{self.owner.name}'s {self.bet_type} bet amount ${self.amount} exceeds the table maximum of ${table_maximum}.")
            return False

        # Check if the bet amount is valid for the bet type
        if self.bet_type in ["Place", "Buy"]:
            if self.amount % self.unit != 0:
                logging.warning(f"{self.owner.name}'s {self.bet_type} bet amount ${self.amount} must be a multiple of ${self.unit}.")
                return False

        return True

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
        raise NotImplementedError("Subclasses must implement this method.")
    
    def __str__(self):
        return f"{self.owner.name}'s ${self.amount} {self.bet_type} bet (Status: {self.status})"