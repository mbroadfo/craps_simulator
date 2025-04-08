from typing import List, Optional, TYPE_CHECKING
from craps.base_strategy import BaseStrategy
from craps.bet import Bet

if TYPE_CHECKING:
    from craps.table import Table
    from craps.game_state import GameState
    from craps.player import Player

class RegressThenPressStrategy(BaseStrategy):
    """
    Composite Strategy: Regress-Then-Press

    This strategy starts with an aggressive regression pattern to lock in profits.
    Once the session profit reaches the original exposure amount, it switches to a
    pressing strategy (e.g., half-press) for the remainder of the session.
    
    Attributes:
        regression: The initial strategy (typically PlaceRegressionStrategy).
        press: The follow-up strategy (e.g. HalfPressStrategy).
        transitioned: Whether the strategy has transitioned to press mode.
        active_strategy: The currently active delegate strategy.
    """

    def __init__(self, regression_strategy: BaseStrategy, press_strategy: BaseStrategy) -> None:
        super().__init__("Regress Then Press")
        self.regression = regression_strategy
        self.press = press_strategy
        self.active_strategy = self.regression
        self.transitioned = False

    def on_new_shooter(self) -> None:
        """Reset both strategies at the start of a new shooter."""
        self.regression.on_new_shooter()
        self.press.on_new_shooter()
        self.active_strategy = self.regression
        self.transitioned = False

    def notify_payout(self, amount: int) -> None:
        """Inform both strategies of a payout and check for transition condition."""
        self.regression.notify_payout(amount)
        self.press.notify_payout(amount)

        if not self.transitioned:
            session_profit = getattr(self.regression, "session_profit", 0)
            exposure = getattr(self.regression, "original_exposure", float("inf"))

            if session_profit >= exposure:
                self.active_strategy = self.press
                self.transitioned = True

    def place_bets(self, game_state: "GameState", player: "Player", table: "Table") -> List[Bet]:
        return self.active_strategy.place_bets(game_state, player, table)

    def adjust_bets(self, game_state: "GameState", player: "Player", table: "Table") -> Optional[List[Bet]]:
        return self.active_strategy.adjust_bets(game_state, player, table)

    def notify_roll(self, game_state: "GameState", player: "Player", table: "Table") -> None:
        return self.active_strategy.notify_roll(game_state, player, table)

    def remove_bets(self, game_state: "GameState", player: "Player", table: "Table") -> Optional[List[Bet]]:
        return self.active_strategy.remove_bets(game_state, player, table)

    def turn_off_bets(self, game_state: "GameState", player: "Player", table: "Table") -> Optional[List[Bet]]:
        return self.active_strategy.turn_off_bets(game_state, player, table)

    def turn_on_bets(self, game_state: "GameState", player: "Player", table: "Table") -> Optional[List[Bet]]:
        return self.active_strategy.turn_on_bets(game_state, player, table)
