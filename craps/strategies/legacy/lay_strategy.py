from __future__ import annotations
from typing import Union, TYPE_CHECKING, Optional, List
from craps.base_strategy import BaseStrategy

if TYPE_CHECKING:
    from craps.table import Table
    from craps.rules_engine import RulesEngine
    from craps.game_state import GameState
    from craps.player import Player
    from craps.bet import Bet

class LayBetStrategy(BaseStrategy):
    """Betting strategy for Lay Bets against point numbers."""

    def __init__(
        self, 
        table: Table, 
        rules_engine: RulesEngine, 
        numbers_or_strategy: Union[str, List[int]],
        strategy_name: Optional[str] = None,
    ) -> None:
        """
        Initialize the Lay Bet strategy.

        :param table: The table object to access current bets.
        :param rules_engine: RulesEngine instance used to create and validate bets.
        :param numbers_or_strategy: A list of numbers (e.g., [4, 10]) or a named group ("outside", "across").
        """
        super().__init__("Lay")
        self.table: Table = table
        self.rules_engine: RulesEngine = rules_engine
        self.numbers_or_strategy: Union[str, List[int]] = numbers_or_strategy
        self.strategy_name = strategy_name or "Lay"

    def place_bets(self, game_state: GameState, player: Player, table: Table) -> List[Bet]:
        """Place Lay bets on selected numbers after the point is established."""
        if game_state.phase != "point":
            return []  # Only bet during the point phase

        rules_engine = table.get_rules_engine()

        # Determine which numbers to lay against
        if isinstance(self.numbers_or_strategy, str):
            strategy = self.numbers_or_strategy.lower()
            if strategy == "outside":
                numbers = [4, 10]
            elif strategy == "inside":
                numbers = [5, 6, 8, 9]
            elif strategy == "across":
                numbers = [4, 5, 6, 8, 9, 10]
            else:
                raise ValueError(f"Invalid lay strategy: {strategy}")
        else:
            numbers = self.numbers_or_strategy

        # Filter out numbers already covered by Lay bets for this player
        numbers_to_bet = [
            num for num in numbers
            if not any(
                bet.owner == player and bet.bet_type == "Lay" and bet.number == num and bet.status == "active"
                for bet in table.bets
            )
        ]

        # Place Lay bets
        bets: List[Bet] = []
        for number in numbers_to_bet:
            min_bet = rules_engine.get_minimum_bet("Lay", table, number=number)
            lay_bet = rules_engine.create_bet("Lay", min_bet, player, number=number)
            bets.append(lay_bet)

        return bets
