from __future__ import annotations  # Enable forward references for type hints
from typing import TYPE_CHECKING, List, Optional
from craps.strategies.free_odds_strategy import FreeOddsStrategy

if TYPE_CHECKING:
    from craps.table import Table  # Prevents circular imports
    from craps.rules_engine import RulesEngine  
    from craps.game_state import GameState
    from craps.player import Player
    from craps.bet import Bet

class ThreePointMollyStrategy:
    """Betting strategy for the 3-Point Molly system."""

    def __init__(self, table: Table, rules_engine: RulesEngine, min_bet: int, odds_type: Optional[str] = None, come_odds_working_on_come_out: bool = False) -> None:
        """
        Initialize the 3-Point Molly strategy.

        :param table: The table object to determine minimum bets.
        :param rules_engine: The RulesEngine instance from the table.
        :param min_bet: The minimum bet amount for the table.
        :param odds_type: The type of odds to use (e.g., "3x-4x-5x").
        :param come_odds_working_on_come_out: Whether Come odds bets are working during the come-out roll.
        """
        self.table = table
        self.rules_engine = rules_engine  # Use existing RulesEngine
        self.min_bet = min_bet
        self.odds_strategy = FreeOddsStrategy(table, odds_type) if odds_type else None  # Delegate odds to FreeOddsStrategy
        self.come_odds_working_on_come_out = come_odds_working_on_come_out

    def get_bet(self, game_state: GameState, player: Player, table: Table) -> Optional[List[Bet]]:
        """
        Place bets according to the 3-Point Molly strategy.

        :param game_state: The current game state.
        :param player: The player placing the bets.
        :param table: The table to place the bets on.
        :return: A list of bets to place, or None if no bets are placed.
        """
        bets: List[Bet] = []

        # Place a Pass Line bet if no active Pass Line bet exists (only during come-out phase)
        if game_state.phase == "come-out":
            if not any(bet.bet_type == "Pass Line" for bet in table.bets if bet.owner == player):
                bets.append(self.rules_engine.create_bet("Pass Line", self.min_bet, player))

        # Place up to 3 Come bets if fewer than 3 active Come bets exist (only during point phase)
        if game_state.phase == "point":
            active_come_bets = [bet for bet in table.bets if bet.bet_type == "Come" and bet.owner == player]
            if len(active_come_bets) < 3:
                bets.append(self.rules_engine.create_bet("Come", self.min_bet, player))

        # Place odds on active Pass Line and Come bets using FreeOddsStrategy
        if self.odds_strategy and game_state.phase == "point":
            odds_bets = self.odds_strategy.get_bet(game_state, player)
            if odds_bets:
                bets.extend(odds_bets)

        return bets if bets else None

    def should_come_odds_be_working(self) -> bool:
        """Return whether the strategy wants Come Odds to be working during the next come-out roll."""
        return self.come_odds_working_on_come_out  # Player-defined setting
