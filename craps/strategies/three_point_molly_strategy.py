from __future__ import annotations
from typing import TYPE_CHECKING, List, Optional
from craps.strategies.free_odds_strategy import FreeOddsStrategy
from craps.base_strategy import BaseStrategy

if TYPE_CHECKING:
    from craps.table import Table
    from craps.rules_engine import RulesEngine  
    from craps.game_state import GameState
    from craps.player import Player
    from craps.bet import Bet

class ThreePointMollyStrategy(BaseStrategy):
    """Betting strategy for the 3-Point Molly system."""

    def __init__(
        self, 
        table: Table, 
        bet_amount: int, 
        odds_type: Optional[str] = None, 
        come_odds_working_on_come_out: bool = False,
        strategy_name: Optional[str] = None,
    ) -> None:
        
        super().__init__(strategy_name or "ThreePointDolly")
        """
        Initialize the 3-Point Molly strategy.

        :param table: The table object to determine minimum bets.
        :param bet_amount: The bet amount for the strategy (defaults to table minimum).
        :param odds_type: The type of odds to use (e.g., "3x-4x-5x").
        :param come_odds_working_on_come_out: Whether Come odds bets are working during the come-out roll.
        """
        self.table = table
        self.bet_amount = bet_amount
        self.odds_strategy = FreeOddsStrategy(table, odds_type) if odds_type else None
        self.come_odds_working_on_come_out = come_odds_working_on_come_out
        self.strategy_name = strategy_name or "ThreePointDolly"

    def place_bets(self, game_state: GameState, player: Player, table: Table) -> List[Bet]:
        """
        Place bets according to the 3-Point Molly strategy.

        :param game_state: The current game state.
        :param player: The player placing the bets.
        :param table: The table to place the bets on.
        :return: A list of bets to place, or None if no bets are placed.
        """
        bets: List[Bet] = []
        rules_engine = table.rules_engine

        # Place a Pass Line bet if no active Pass Line bet exists (only during come-out phase)
        if game_state.phase == "come-out":
            if not player.has_active_bet(table, "Pass Line"):
                bets.append(rules_engine.create_bet("Pass Line", self.bet_amount, player))

        # Place up to 2 Come bets if fewer than 2 active Come bets (with a number) exist (only during point phase)
        if game_state.phase == "point":
            active_come_bets = [
                bet for bet in table.bets
                if bet.bet_type == "Come" and bet.owner == player and bet.number is not None
            ]
            if len(active_come_bets) < 2:
                bets.append(rules_engine.create_bet("Come", self.bet_amount, player))

        # Place odds on active Pass Line and Come bets using FreeOddsStrategy
        if self.odds_strategy and game_state.phase == "point":
            odds_bets = self.odds_strategy.get_odds_bet(game_state, player, table)
            if odds_bets:
                existing_odds = {
                    (bet.parent_bet, bet.number)
                    for bet in table.bets
                    if bet.bet_type.endswith("Odds") and bet.owner == player
                }
                for odds_bet in odds_bets:
                    parent = odds_bet.parent_bet
                    if (
                        parent
                        and parent.owner == player
                        and (parent, parent.number) not in existing_odds
                    ):
                        odds_bet.number = parent.number  # Ensure odds bet inherits number
                        bets.append(odds_bet)

        return bets if bets else []

    def should_come_odds_be_working(self) -> bool:
        """Return whether the strategy wants Come Odds to be working during the next come-out roll."""
        return self.come_odds_working_on_come_out
