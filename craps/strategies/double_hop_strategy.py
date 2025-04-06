from __future__ import annotations
from typing import TYPE_CHECKING, List
from craps.bet import Bet
from craps.base_strategy import BaseStrategy
from craps.bet_adjusters import PressAdjuster

if TYPE_CHECKING:
    from craps.rules_engine import RulesEngine
    from craps.game_state import GameState
    from craps.player import Player
    from craps.table import Table

class DoubleHopStrategy(BaseStrategy):
    def __init__(self, hop_target: tuple[int, int], rules_engine: RulesEngine, base_bet: int) -> None:
        super().__init__("Double Hop")
        self.hop_target = hop_target
        self.rules_engine = rules_engine
        self.base_bet = base_bet
        self.pressed_once = False  # <-- track press state
        self.adjuster = PressAdjuster()

    def place_bets(self, game_state: GameState, player: Player, table: Table) -> List[Bet]:
        # Only place the bet if it's not already present
        existing = next(
            (b for b in table.bets if b.owner == player and b.bet_type == "Hop" and b.number == self.hop_target),
            None
        )

        if not existing:
            bet = self.rules_engine.create_bet("Hop", self.base_bet, player, number=self.hop_target)
            if game_state.play_by_play is not None:
                player.place_bet(bet, table, game_state.phase, game_state.play_by_play)

        return []

    def adjust_bets(self, game_state: GameState, player: Player, table: Table) -> List[Bet]:
        for bet in table.bets:
            if bet.owner == player and bet.bet_type == "Hop" and bet.number == self.hop_target:
                if bet.status == "won":
                    if bet.hits % 2 == 1:
                        # First, third, fifth win → press
                        self.adjuster.adjust(bet, table, self.rules_engine)
                    else:
                        # Second, fourth, sixth win → reset
                        bet.amount = self.base_bet

        return []
