from typing import List, Optional, TYPE_CHECKING
from craps.bet import Bet
from craps.base_strategy import BaseStrategy
from craps.bet_adjusters import BetAdjuster

if TYPE_CHECKING:
    from craps.table import Table
    from craps.player import Player
    from craps.game_state import GameState

class AdjusterOnlyStrategy(BaseStrategy):
    """
    Generic wrapper strategy that delegates adjust_bets() to a BetAdjuster.
    Used when bet placement is handled by another strategy.
    """

    def __init__(
            self, 
            name: str, 
            adjuster: BetAdjuster,
            #strategy_name: Optional[str] = None,
            ) -> None:
        
        super().__init__(name)
        self.adjuster = adjuster
        self.last_game_state: Optional["GameState"] = None
        self.last_player: Optional["Player"] = None
        self.last_table: Optional["Table"] = None
        #self.strategy_name = strategy_name or "Adjuster"

    def place_bets(self, game_state: "GameState", player: "Player", table: "Table") -> List[Bet]:
        return []

    def adjust_bets(self, game_state: "GameState", player: "Player", table: "Table") -> Optional[List[Bet]]:
        self.last_game_state = game_state
        self.last_player = player
        self.last_table = table

        updated: List[Bet] = []
        for bet in table.bets:
            if bet.owner == player and bet.bet_type == "Place" and bet.status == "won":
                self.adjuster.adjust(bet, table, table.rules_engine)
                updated.append(bet)
        return updated if updated else None

    def on_new_shooter(self) -> None:
        """Reset internal state if adjuster supports it."""
        if self.last_game_state and self.last_player and self.last_table:
            self.adjuster.on_new_shooter(self.last_game_state, self.last_player, self.last_table)
