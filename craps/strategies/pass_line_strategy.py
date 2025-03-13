from __future__ import annotations  # Enable forward references for type hints
from typing import TYPE_CHECKING, Optional
from craps.bet import Bet

if TYPE_CHECKING:
    from craps.rules_engine import RulesEngine  
    from craps.game_state import GameState
    from craps.player import Player
    from craps.table import Table

class PassLineStrategy:
    """Betting strategy for Pass Line bets."""
    
    def __init__(self, min_bet: int) -> None:
        """
        Initialize the Pass Line Strategy.

        :param min_bet: Minimum bet required for Pass Line.
        """
        self.min_bet: int = min_bet  # Fixed type
        self.rules_engine: RulesEngine = RulesEngine()  # Initialize RulesEngine

    def get_bet(self, game_state: GameState, player: Player, table: Table) -> Optional[Bet]:
        """
        Place a Pass Line bet during the come-out roll if no active bet exists.

        :param game_state: The current game state.
        :param player: The player placing the bet.
        :param table: The table where the bet will be placed.
        :return: A Pass Line bet or None if no bet is placed.
        """
        if game_state.phase == "come-out":
            # Check if the player already has an active Pass Line bet
            if player.has_active_bet(table, "Pass Line"):
                return None  # No new bet to place

            # Use RulesEngine to create a Pass Line bet
            return self.rules_engine.create_bet("Pass Line", self.min_bet, player)
        
        return None  # No bet to place