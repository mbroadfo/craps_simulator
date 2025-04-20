from __future__ import annotations
from typing import TYPE_CHECKING, List, Optional
from craps.bet import Bet
from craps.base_strategy import BaseStrategy
from craps.bet_adjusters import PressStyle, PressAdjuster

if TYPE_CHECKING:
    from craps.rules_engine import RulesEngine
    from craps.game_state import GameState
    from craps.player import Player
    from craps.table import Table

class DoubleHopStrategy(BaseStrategy):
    def __init__(
            self, 
            hop_target: tuple[int, int], 
            rules_engine: RulesEngine, 
            base_bet: int,
            strategy_name: Optional[str] = None,
    ) -> None:
        super().__init__("Double Hop")
        self.hop_target = hop_target
        self.rules_engine = rules_engine
        self.base_bet = base_bet
        self.pressed_once = False  # <-- track press state
        self.press_adjuster = PressAdjuster(style=PressStyle.FULL),
        self.strategy_name = strategy_name or "DoubleHop"        

    def place_bets(self, game_state: GameState, player: Player, table: Table) -> List[Bet]:
        bet = self.rules_engine.create_bet("Hop", self.base_bet, player, self.hop_target)
        return [bet]

    def adjust_bets(self, game_state: GameState, player: Player, table: Table) -> Optional[List[Bet]]:
        updated = []

        for bet in table.bets:
            if bet.owner == player and bet.bet_type == "Hop" and bet.number == self.hop_target:
                if bet.status == "won":
                    if bet.hits == 1:
                        self.press_adjuster.adjust(bet, table, self.rules_engine)  # ✅ First hit → press it
                        updated.append(bet)
                    elif bet.hits >= 2:
                        bet.amount = self.base_bet  # ✅ Reset on second win
                        updated.append(bet)

        return updated if updated else None