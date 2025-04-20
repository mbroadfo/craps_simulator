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

class ThreePointDollyStrategy(BaseStrategy):
    """
    Betting strategy for the 3-Point Dolly system.

    This strategy plays the dark side of the 3-point molly:
    - A Don't Pass bet on come-out
    - Up to 2 Don't Come bets with lay odds
    """

    def __init__(
        self,
        table: Table,
        bet_amount: int,
        odds_type: Optional[str] = "3x4x5x",
        dont_come_odds_working_on_come_out: bool = False,
        strategy_name: Optional[str] = None,
    ) -> None:
        
        super().__init__(strategy_name or "ThreePointMolly")
        self.table = table
        self.bet_amount = bet_amount
        self.odds_strategy = FreeOddsStrategy(table, odds_type) if odds_type else None
        self.dont_come_odds_working_on_come_out = dont_come_odds_working_on_come_out
        self.strategy_name = strategy_name or "ThreePointMolly"

    def place_bets(self, game_state: GameState, player: Player, table: Table) -> List[Bet]:
        bets: List[Bet] = []
        rules_engine = table.rules_engine

        # Place Don't Pass on come-out if not already placed
        if game_state.phase == "come-out":
            if not player.has_active_bet(table, "Don't Pass"):
                bets.append(rules_engine.create_bet("Don't Pass", self.bet_amount, player))

        # Place up to 2 Don't Come bets during point phase
        if game_state.phase == "point":
            active_dont_come_bets = [
                b for b in table.bets
                if b.bet_type == "Don't Come" and b.owner == player and b.number is not None
            ]
            if len(active_dont_come_bets) < 2:
                bets.append(rules_engine.create_bet("Don't Come", self.bet_amount, player))

        # Place Lay Odds on Don't Pass and Don't Come bets using FreeOddsStrategy
        if self.odds_strategy and game_state.phase == "point":
            odds_bets = self.odds_strategy.get_odds_bet(game_state, player, table)
            if odds_bets:
                existing_odds = {
                    (b.parent_bet, b.number)
                    for b in table.bets
                    if b.bet_type.endswith("Odds") and b.owner == player
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

    def should_dont_come_odds_be_working(self) -> bool:
        """
        Return whether the strategy wants Don't Come odds to be working during the next come-out roll.
        """
        return self.dont_come_odds_working_on_come_out
