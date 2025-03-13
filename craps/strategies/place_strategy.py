from __future__ import annotations  # Enable forward references for type hints
from typing import Union, TYPE_CHECKING, Optional, List

if TYPE_CHECKING:
    from craps.table import Table  # Prevents circular imports
    from craps.rules_engine import RulesEngine
    from craps.game_state import GameState
    from craps.player import Player
    from craps.bet import Bet

class PlaceBetStrategy:
    """Betting strategy for Place Bets."""

    def __init__(self, table: Table, numbers_or_strategy: Union[str, list[int]]):
        """
        Initialize the Place Bet strategy.

        :param table: The table object to determine minimum bets.
        :param numbers_or_strategy: A list of numbers (e.g., [5, 6, 8, 9]) or a strategy ("inside", "across").
        """
        self.table: Table = table
        self.numbers_or_strategy: Union[str, list[int]] = numbers_or_strategy
        self.rules_engine: RulesEngine = RulesEngine()  # Initialize RulesEngine

    def get_bet(self, game_state: GameState, player: Player, table: Table) -> Optional[List[Bet]]:
        """Place Place Bets based on the strategy and game state."""
        if game_state.phase != "point":
            return None  # Only place bets after the point is established

        # Determine which numbers to bet on
        if isinstance(self.numbers_or_strategy, str):
            if self.numbers_or_strategy == "inside":
                numbers = [5, 6, 8, 9]  # Inside numbers
            elif self.numbers_or_strategy == "across":
                numbers = [4, 5, 6, 8, 9, 10]  # Across numbers
            else:
                raise ValueError(f"Invalid strategy: {self.numbers_or_strategy}")
        else:
            numbers = self.numbers_or_strategy  # Specific numbers provided

        # Filter out numbers already covered by a Pass Line bet or a Place bet
        numbers = [
            num for num in numbers
            if not any(
                (bet.owner == player and bet.bet_type == "Pass Line" and bet.point == num) or  # Pass Line covers the point
                (bet.owner == player and bet.bet_type.startswith("Place") and bet.number == num)  # Place Bet covers the number
                for bet in table.bets
            )
        ]

        # Use RulesEngine to create Place bets
        bets: List[Bet] = []
        for number in numbers:
            min_bet = self.table.get_minimum_bet(number)
            bets.append(self.rules_engine.create_bet("Place", min_bet, player, number=number))

        return bets if bets else None
