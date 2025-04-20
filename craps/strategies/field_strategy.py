from __future__ import annotations
from typing import TYPE_CHECKING, List, Optional
from craps.base_strategy import BaseStrategy

if TYPE_CHECKING:
    from craps.rules_engine import RulesEngine  # Prevents circular imports
    from craps.game_state import GameState
    from craps.player import Player
    from craps.table import Table
    from craps.bet import Bet

class FieldBetStrategy(BaseStrategy):
    """Betting strategy for Field bets."""
    
    def __init__(
            self, 
            min_bet: int,
            strategy_name: Optional[str] = None,
        ) -> None:
        """
        Initialize the Field Bet strategy.
        
        :param min_bet: The minimum bet amount for the table.
        """
        super().__init__("Field")
        self.min_bet: int = min_bet
        self.strategy_name = strategy_name or "Field"

    def place_bets(self, game_state: GameState, player: Player, table: Table) -> List[Bet]:
        """
        Place a Field bet during the point roll if no active bet exists.

        :param game_state: The current game state.
        :param player: The player placing the bet.
        :param table: The table where bets are placed.
        :return: A Field bet if one does not already exist, otherwise None.
        """
        # Check if the player already has an active Field bet
        if player.has_active_bet(table, "Field"):
            return []  # No new bet to place

        # Use RulesEngine to create a Field bet
        rules_engine = table.get_rules_engine()
        return [rules_engine.create_bet("Field", self.min_bet, player)]
