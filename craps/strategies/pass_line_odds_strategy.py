from __future__ import annotations  # Enable forward references for type hints
from typing import TYPE_CHECKING, Optional
from craps.bet import Bet

if TYPE_CHECKING:
    from craps.table import Table  # Prevents circular imports
    from craps.rules_engine import RulesEngine
    from craps.game_state import GameState
    from craps.player import Player

class PassLineOddsStrategy:
    """Betting strategy for Pass Line with Odds bets."""

    def __init__(self, table: Table, odds_multiple: int = 1) -> None:
        """
        Initialize the Pass Line Odds strategy.
        
        :param table: The table object to determine minimum bets.
        :param odds_multiple: The multiple of the minimum bet to use for odds (e.g., 1x, 2x).
        """
        self.table: Table = table
        self.odds_multiple: int = odds_multiple  # Fixed type
        self.rules_engine: RulesEngine = RulesEngine()  # Initialize RulesEngine

    def get_bet(self, game_state: GameState, player: Player, table: Table) -> Optional[Bet]:
        """
        Place a Pass Line or Pass Line Odds bet based on the game state.

        :param game_state: The current game state.
        :param player: The player placing the bet.
        :param table: The table where the bet will be placed.
        :return: A Pass Line or Pass Line Odds bet, or None if no bet is placed.
        """
        if game_state.phase not in ["come-out", "point"]:
            return None  # Do not place the bet if the phase is invalid

        if game_state.phase == "come-out":
            # Check if the player already has an active Pass Line bet
            if player.has_active_bet(table, "Pass Line"):
                return None  # No new bet to place

            # Use RulesEngine to create a Pass Line bet
            return self.rules_engine.create_bet("Pass Line", self.table.house_rules.table_minimum, player)
        
        elif game_state.phase == "point":
            # Check if the player already has an active Pass Line Odds bet
            if player.has_active_bet(table, "Pass Line Odds"):
                return None  # No new bet to place

            # Find the player's active Pass Line bet
            pass_line_bet = next(
                (bet for bet in table.bets if bet.owner == player and bet.bet_type == "Pass Line"),
                None
            )
            if pass_line_bet is None:
                return None  # No Pass Line bet found

            # Use RulesEngine to create a Pass Line Odds bet linked to the Pass Line bet
            return self.rules_engine.create_bet(
                "Pass Line Odds",
                self.table.house_rules.table_minimum * self.odds_multiple,  # Bet amount
                player,  # Owner
                number=game_state.point,  # Pass the current point number
                parent_bet=pass_line_bet  # Parent Pass Line bet
            )
        
        return None  # No bet to place