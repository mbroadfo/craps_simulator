from __future__ import annotations  # Enable forward references for type hints
from typing import TYPE_CHECKING, List, Optional
from craps.bet import Bet
from craps.game_state import GameState

if TYPE_CHECKING:
    from craps.player import Player
    from craps.table import Table

class FreeOddsStrategy:
    """Betting strategy for Free Odds on any active bet."""

    def __init__(
            self, 
            table: Table, 
            odds_type: Optional[str] = None,
            strategy_name: Optional[str] = None,
        ) -> None:
        """
        Initialize the Free Odds strategy.

        :param table: The table instance to use for rules validation.
        :param odds_type: The type of odds to use (e.g., "3x-4x-5x").
        """
        self.table = table
        self.odds_type = odds_type
        self.strategy_name = strategy_name or "FreeOdds"

    def get_odds_bet(self, game_state: GameState, player: Player, table: Table) -> Optional[List[Bet]]:
        """
        Place Free Odds bets on any active bets for the player.

        :param game_state: The current game state.
        :param player: The player placing the bet.
        :return: A list of odds bets to place, or None if no bets are placed.
        """
        if game_state.phase != "point" or not self.odds_type:
            return None  # No odds bets if there's no point or no odds strategy

        bets = []
        rules_engine = table.rules_engine

        # Retrieve active Pass Line or Come bets belonging to the player
        active_bets = [bet for bet in table.bets if bet.owner == player]

        for active_bet in active_bets:
            if active_bet.is_contract_bet:
                # Determine the relevant point number
                if active_bet.bet_type in ["Pass Line", "Don't Pass"]:
                    point_number = game_state.point
                elif active_bet.bet_type in ["Come", "Don't Come"]:
                    point_number = active_bet.number if isinstance(active_bet.number, int) else None
                else:
                    point_number = None

                multiplier = rules_engine.get_odds_multiplier(self.odds_type, point_number)

                if multiplier is None:
                    continue  # Skip if no valid multiplier

                # Determine the correct odds bet amount
                odds_amount = min(active_bet.amount * multiplier, player.balance)

                # Create the odds bet using the Rules Engine
                bets.append(rules_engine.create_bet(
                    f"{active_bet.bet_type} Odds",
                    odds_amount,
                    player,
                    parent_bet=active_bet
                ))

        return bets if bets else None
