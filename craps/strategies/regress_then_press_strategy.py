from typing import List, Optional, TYPE_CHECKING
from craps.base_strategy import BaseStrategy
from craps.bet import Bet
from craps.bet_adjusters import PressAdjuster, PressStyle
from craps.strategies.adjuster_only_strategy import AdjusterOnlyStrategy

if TYPE_CHECKING:
    from craps.table import Table
    from craps.game_state import GameState
    from craps.player import Player


class RegressThenPressStrategy(BaseStrategy):
    """
    Composite Strategy: Regress-Then-Press

    This strategy begins each shooter by executing a regression-style betting pattern
    designed to quickly reduce risk after initial bets are placed.

    After the total session profit reaches the original exposure level for the current shooter,
    the strategy transitions to a more aggressive approach, such as pressing bets
    (e.g., half-pressing winnings).

    Once in press mode, it remains active until pressed up to the original high-bet amount. It
    then switches back to regression mode where the cycle repeats.
    """

    def __init__(
        self, 
        regression_strategy: BaseStrategy, 
        press_style: Optional[PressStyle] = None,
        strategy_name: Optional[str] = None,
    ) -> None:
        
        super().__init__("Regress Then Press")
        self.regression = regression_strategy
        self.press = AdjusterOnlyStrategy(
            name=f"{(press_style or PressStyle.HALF).value.title()} Press",
            adjuster=PressAdjuster(style=(press_style or PressStyle.HALF))
        )
        self.active_strategy = self.regression
        self.transitioned = False
        self.max_press_threshold: Optional[float] = None
        self.strategy_name = strategy_name or "RegressThenPress"

    def on_new_shooter(self) -> None:
        self.regression.on_new_shooter()
        self.press.on_new_shooter()
        self.active_strategy = self.regression
        self.transitioned = False
        self.max_press_threshold = None

    def notify_payout(self, amount: int) -> None:
        self.regression.notify_payout(amount)
        self.press.notify_payout(amount)

    def place_bets(self, game_state: "GameState", player: "Player", table: "Table") -> List[Bet]:
        return self.active_strategy.place_bets(game_state, player, table)

    def adjust_bets(self, game_state: "GameState", player: "Player", table: "Table") -> Optional[List[Bet]]:
        if self.transitioned and self.max_press_threshold is not None:
            total_on_table = sum(
                bet.amount for bet in table.bets
                if bet.owner == player and bet.bet_type == "Place" and bet.number in {5, 6, 8, 9}
            )
            if total_on_table >= self.max_press_threshold:
                self.active_strategy = self.regression
                self.transitioned = False
                self.regression.reset_shooter_state()
        return self.active_strategy.adjust_bets(game_state, player, table)

    def notify_roll(self, game_state: "GameState", player: "Player", table: "Table") -> None:
        return self.active_strategy.notify_roll(game_state, player, table)

    def remove_bets(self, game_state: "GameState", player: "Player", table: "Table") -> Optional[List[Bet]]:
        return self.active_strategy.remove_bets(game_state, player, table)

    def turn_off_bets(self, game_state: "GameState", player: "Player", table: "Table") -> Optional[List[Bet]]:
        return self.active_strategy.turn_off_bets(game_state, player, table)

    def turn_on_bets(self, game_state: "GameState", player: "Player", table: "Table") -> Optional[List[Bet]]:
        return self.active_strategy.turn_on_bets(game_state, player, table)
