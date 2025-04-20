from __future__ import annotations  # Enable forward references for type hints
from typing import TYPE_CHECKING, List, Optional
from craps.bet import Bet
from craps.base_strategy import BaseStrategy
from craps.strategies.free_odds_strategy import FreeOddsStrategy

if TYPE_CHECKING:
    from craps.game_state import GameState
    from craps.player import Player
    from craps.table import Table

class PassLineStrategy(BaseStrategy):
    """Pass Line betting strategy with optional odds."""

    def __init__(
        self, 
        bet_amount: int, 
        table: Table, 
        odds_type: Optional[str] = None,
        strategy_name: Optional[str] = None,
    ) -> None:
        """
        Initialize the Pass Line strategy.

        :param bet_amount: The base amount to bet on the Pass Line.
        :param table: The Table instance for placing bets.
        :param odds_type: Optional string specifying the odds type (e.g., "3x-4x-5x").
        """
        super().__init__("Pass Line")
        self.bet_amount = bet_amount
        self.table = table
        self.odds_strategy = FreeOddsStrategy(table, odds_type) if odds_type else None
        self.strategy_name = strategy_name or "PassLine"

    def place_bets(self, game_state: GameState, player: Player, table: Table) -> List[Bet]:
        """Place a Pass Line bet at the start of the come-out roll."""
        if game_state.phase == "come-out" and not player.has_active_bet(table, "Pass Line"):
            return [table.rules_engine.create_bet("Pass Line", self.bet_amount, player)]
        return []

    def adjust_bets(self, game_state: GameState, player: Player, table: Table) -> Optional[List[Bet]]:
        """If an odds strategy is set, place odds bets when a point is established."""
        if self.odds_strategy and game_state.phase == "point":
            return self.odds_strategy.get_odds_bet(game_state, player, table)  # Delegate odds betting to FreeOddsStrategy
        return None
