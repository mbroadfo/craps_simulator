# File: .\craps\strategies\field_strategy.py

from __future__ import annotations
from typing import TYPE_CHECKING, Optional
if TYPE_CHECKING:
    from craps.rules_engine import RulesEngine  # Prevents circular imports
    from craps.game_state import GameState
    from craps.player import Player
    from craps.table import Table
    from craps.bet import Bet

class FieldBetStrategy:
    """Betting strategy for Field bets."""
    
    def __init__(self, min_bet: int) -> None:
        """
        Initialize the Field Bet strategy.
        
        :param min_bet: The minimum bet amount for the table.
        """
        self.min_bet: int = min_bet
        self.rules_engine: RulesEngine = RulesEngine()  # Initialize RulesEngine

    def get_bet(self, game_state: GameState, player: Player, table: Table) -> Optional[Bet]:
        """
        Place a Field bet during the point roll if no active bet exists.

        :param game_state: The current game state.
        :param player: The player placing the bet.
        :param table: The table where bets are placed.
        :return: A Field bet if one does not already exist, otherwise None.
        """
        if game_state.phase != "point":
            return None  # Only place bets after the point is established
        
        # Check if the player already has an active Field bet
        if player.has_active_bet(table, "Field"):
            return None  # No new bet to place

        # Use RulesEngine to create a Field bet
        return self.rules_engine.create_bet("Field", self.min_bet, player)
