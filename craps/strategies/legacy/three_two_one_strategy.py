from __future__ import annotations
from typing import TYPE_CHECKING, List, Optional
from craps.bet import Bet
from craps.base_strategy import BaseStrategy
from craps.bet_adjusters import PressAdjuster

if TYPE_CHECKING:
    from craps.rules_engine import RulesEngine
    from craps.game_state import GameState
    from craps.player import Player
    from craps.table import Table

class ThreeTwoOneStrategy(BaseStrategy):
    def __init__(
        self, 
        rules_engine: RulesEngine, 
        min_bet: int, 
        odds_type: str = "2x",
        strategy_name: Optional[str] = None,
    ) -> None:
        
        super().__init__("Three-Two-One")
        self.rules_engine = rules_engine
        self.min_bet = min_bet
        self.odds_type = odds_type
        self.total_hits = 0
        self.adjuster = PressAdjuster()
        self.turned_off = False
        self.strategy_name = strategy_name or "ThreeTwoOne"

    def place_bets(self, game_state: GameState, player: Player, table: Table) -> List[Bet]:
        new_bets = []
        
        if game_state.phase == "come-out":
            # Only place Pass Line bet
            new_passline_bet = self.rules_engine.create_bet("Pass Line", self.min_bet, player)
            new_bets.append(new_passline_bet)
        else:
            # Add odds only if not already added
            has_odds = any(
                b.bet_type == "Pass Line Odds" and b.owner == player for b in table.bets
            )
            if not has_odds:
                for bet in table.bets:
                    if bet.bet_type == "Pass Line" and bet.owner == player:
                        multiplier = self.rules_engine.get_odds_multiplier(self.odds_type, game_state.point) or 0
                        odds_amount = self.min_bet * multiplier
                        odds_bet = self.rules_engine.create_bet("Pass Line Odds", odds_amount, player)
                        odds_bet.parent_bet = bet  # ✅ Critical: link odds to Pass Line
                        new_bets.append(odds_bet)

            # Place inside numbers (excluding the point)
            inside_numbers = [5, 6, 8, 9]
            for num in inside_numbers:
                if num == game_state.point:
                    continue
                existing = next(
                    (b for b in table.bets if b.owner == player and b.bet_type == "Place" and b.number == num),
                    None
                )
                if not existing:
                    amount = self.rules_engine.get_minimum_bet("Place", table, num)
                    inside_bet = self.rules_engine.create_bet("Place", amount, player, num)
                    new_bets.append(inside_bet)
                elif existing.status == "inactive":
                    existing.status = "active"

        return new_bets

    def adjust_bets(self, game_state: GameState, player: Player, table: Table) -> Optional[List[Bet]]:
        # Avoid adjusting during cleanup after 7-out
        if game_state.phase != "come-out" and game_state.point is None:
            return []

        if game_state.phase == "come-out":
            self.total_hits = 0
            self.turned_off = False
            return []

        for bet in table.bets:
            if bet.owner == player and bet.bet_type == "Place" and bet.status == "won":
                self.total_hits += 1
                bet.status = "active"

        if not self.turned_off:
            for bet in table.bets:
                if (
                    bet.bet_type == "Place" and bet.owner == player and
                    (game_state.point in {4, 10} and self.total_hits >= 2 or
                    game_state.point in {5, 6, 8, 9} and self.total_hits >= 3)
                ):
                    self.turned_off = True
                    bet.status = "inactive"

        return None

    def reset_shooter_state(self) -> None:
        """Reset stateful tracking for a new shooter (used by composite strategies)."""
        self.total_hits = 0
        self.turned_off = False
