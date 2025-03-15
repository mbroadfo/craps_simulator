from enum import Enum
from __future__ import annotations
from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    from craps.table import Table
    from craps.rules_engine import RulesEngine
    from craps.game_state import GameState
    from craps.player import Player
    from craps.bet import Bet

class OddsMultiple(Enum):
    ONE_X = "1x"
    TWO_X = "2x"
    THREE_X = "3x"
    ONE_TWO_THREE = "1-2-3"
    THREE_FOUR_FIVE = "3-4-5"

class FreeOddsStrategy:
    """Betting strategy for Free Odds on any active bet."""

    def __init__(self, table: Table, odds_multiple: OddsMultiple = OddsMultiple.ONE_X) -> None:
        """
        Initialize the Free Odds strategy.

        :param table: The table object to determine minimum bets.
        :param odds_multiple: Enum representing odds multiple.
        """
        self.table: Table = table
        self.odds_multiple: OddsMultiple = odds_multiple

    def get_odds_amount(self, original_bet_amount: int) -> int:
        """Calculate the odds amount based on the original bet amount and the selected multiple."""
        if self.odds_multiple == OddsMultiple.ONE_X:
            return original_bet_amount
        elif self.odds_multiple == OddsMultiple.TWO_X:
            return original_bet_amount * 2
        elif self.odds_multiple == OddsMultiple.THREE_X:
            return original_bet_amount * 3
        elif self.odds_multiple == OddsMultiple.ONE_TWO_THREE:
            return original_bet_amount
        elif self.odds_multiple == OddsMultiple.THREE_FOUR_FIVE:
            return original_bet_amount
        else:
            raise ValueError(f"Invalid odds multiple: {self.odds_multiple}")

    def get_bet(self, game_state: GameState, player: Player) -> Optional[List[Bet]]:
        """
        Place Free Odds bets on any active bets for the player.
        
        :param game_state: The current game state.
        :param player: The player placing the bet.
        :return: A list of bets to place, or None if no bets are placed.
        """
        bets: List[Bet] = []
        rules_engine = self.table.get_rules_engine()

        # Retrieve active bets belonging to the player from the table
        active_bets = [bet for bet in self.table.bets if bet.owner == player]

        for active_bet in active_bets:
            if active_bet.bet_type in ["Pass Line", "Place"]:
                odds_amount = self.get_odds_amount(active_bet.amount)

                if active_bet.bet_type == "Pass Line":
                    bets.append(rules_engine.create_bet(
                        "Pass Line Odds", odds_amount, player, parent_bet=active_bet
                    ))
                elif active_bet.bet_type == "Place":
                    bets.append(rules_engine.create_bet(
                        "Place Odds", odds_amount, player, number=active_bet.number, parent_bet=active_bet
                    ))

        return bets if bets else None  # Return bets if any were created
