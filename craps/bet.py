from __future__ import annotations  # Enable forward references for type hints
from typing import TYPE_CHECKING, List, Optional, Tuple, Union
import logging

if TYPE_CHECKING:
    from craps.player import Player  # Prevent circular imports
    from craps.rules_engine import RulesEngine  # Ensure correct type hint for resolve method

class Bet:
    """Represents a single bet in the game of Craps."""

    VALID_PHASES: List[str] = ["come-out", "point"]  # Ensures class-level definition

    def __init__(
        self,
        bet_type: str,
        amount: int,
        owner: Player,
        payout_ratio: Tuple[int, int],  # Updated to a tuple
        locked: bool = False,
        vig: bool = False,  # Updated to a boolean
        unit: int = 1,
        valid_phases: Optional[List[str]] = None,
        number: Optional[Union[int, Tuple[int, int]]] = None,  # ✅ Now supports tuples for Hop bets
        parent_bet: Optional[Bet] = None,
        linked_bet: Optional["Bet"] = None,
        is_contract_bet: bool = False
    ) -> None:
        """
        Initializes a Bet.

        :param number: The number associated with the bet (e.g., 6 for Place 6 or (2,5) for Hop bets).
        """
        self.bet_type: str = bet_type
        self.amount: int = amount
        self.owner: Player = owner
        self.payout_ratio: Tuple[int, int] = payout_ratio  # Ensuring payout is stored as a ratio tuple
        self.locked: bool = locked
        self.vig: bool = vig  # Vig is now a boolean
        self.unit: int = unit
        self.valid_phases: List[str] = valid_phases if valid_phases is not None else self.VALID_PHASES
        self.number: Optional[Union[int, Tuple[int, int]]] = number  # ✅ Now supports both int and tuple
        self.status: str = "active"
        self.parent_bet: Optional[Bet] = parent_bet
        self.is_contract_bet: bool = is_contract_bet  # Whether the bet is a contract bet
        self.linked_bet: Optional[Bet] = linked_bet
        self.resolved_payout: int = 0

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

    def resolve(self, rules_engine: RulesEngine, dice_outcome: Tuple[int, int], phase: str, point: Optional[int]) -> None:
        """
        Resolve the bet based on the dice outcome, phase, and point.
        Delegates resolution logic to the RulesEngine.

        :param rules_engine: The RulesEngine instance to use for resolution.
        :param dice_outcome: The result of the dice roll (e.g., [3, 4]).
        :param phase: The current game phase ("come-out" or "point").
        :param point: The current point number (if in point phase).
        """
        self.resolved_payout = rules_engine.resolve_bet(self, dice_outcome, phase, point)

    def is_resolved(self) -> bool:
        """Check if the bet has been resolved (won, lost, or pushed)."""
        return self.status in ["won", "lost", "pushed"]

    def payout(self) -> int:
        """
        Calculate the payout for the bet.
        - Contract bets return original bet amount + winnings.
        - Non-contract bets return only winnings.
        """
        if self.status != "won":
            return 0  # No payout if the bet was lost

        if self.resolved_payout:
            return self.resolved_payout
        numerator, denominator = self.payout_ratio
        return (self.amount * numerator) // denominator

    def __str__(self) -> str:
        """Return a string representation of the bet."""
        if self.number is not None:
            return f"{self.owner.name}'s ${self.amount} {self.bet_type} {self.number} bet (Status: {self.status})"
        else:
            return f"{self.owner.name}'s ${self.amount} {self.bet_type} bet (Status: {self.status})"
