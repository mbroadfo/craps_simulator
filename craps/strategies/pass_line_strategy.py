from __future__ import annotations  # Enable forward references for type hints
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from craps.rules_engine import RulesEngine  

class PassLineStrategy:
    """Betting strategy for Pass Line bets."""
    def __init__(self, min_bet):
        self.min_bet: str = min_bet
        self.rules_engine: RulesEngine = RulesEngine()  # Initialize RulesEngine

    def get_bet(self, game_state, player, table):
        """Place a Pass Line bet during the come-out roll if no active bet exists."""
        if game_state.phase == "come-out":
            # Check if the player already has an active Pass Line bet
            if player.has_active_bet(table, "Pass Line"):
                return None  # No new bet to place

            # Use RulesEngine to create a Pass Line bet
            return self.rules_engine.create_bet("Pass Line", self.min_bet, player)
        return None  # No bet to place