from typing import List, Optional, Set, TYPE_CHECKING, Literal
from craps.bet import Bet
from craps.player import Player
from craps.game_state import GameState
from craps.rules_engine import RulesEngine
from craps.base_strategy import BaseStrategy
from craps.bet_adjusters import BetAdjuster, RegressAdjuster, HalfPressAdjuster

if TYPE_CHECKING:
    from craps.table import Table

class PlaceRegressionStrategy(BaseStrategy):
    """
    Session-aware Place Regression Strategy:
    - Start with high-unit inside bets (e.g. 440)
    - Regress after each inside hit
    - Switch to pressing after session profit buffer is met
    """

    def __init__(self, high_unit: int = 10, low_unit: int = 2, regression_factor: int = 2) -> None:
        super().__init__("Place Regression")

        self.high_unit = high_unit
        self.low_unit = low_unit
        self.regression_factor = regression_factor
        self.unit_levels: List[int] = self._generate_unit_levels()

        self.inside_numbers: Set[int] = {5, 6, 8, 9}
        self.original_exposure: int = self._calculate_total_exposure(self.high_unit)

        # Session state
        self.session_profit: int = 0
        self.mode: Literal["regress", "press"] = "regress"

        # Shooter state
        self.level: int = 0
        self.hits: int = 0
        self.placed: bool = False

    def _generate_unit_levels(self) -> List[int]:
        """Generate unit steps from high to low using the regression factor."""
        levels = [self.high_unit]
        while levels[-1] > self.low_unit:
            next_level = max(self.low_unit, levels[-1] // self.regression_factor)
            if next_level == levels[-1]:
                break
            levels.append(next_level)
        return levels

    def _calculate_total_exposure(self, unit: int) -> int:
        """
        Calculate total inside exposure using the given unit:
        - $5 units on 5/9 (×2)
        - $6 units on 6/8 (×2)
        """
        return unit * 5 * 2 + unit * 6 * 2

    def reset_shooter_state(self) -> None:
        """Reset state that resets every shooter."""
        self.level = 0
        self.hits = 0
        self.placed = False
        self.mode = "regress"

    def on_new_shooter(self) -> None:
        """Called at start of new shooter."""
        self.reset_shooter_state()

    def notify_payout(self, amount: int) -> None:
        """Track hit count and prepare for mode switch after completing regression."""
        self.hits += 1

    def place_bets(self, game_state: GameState, player: Player, table: "Table") -> List[Bet]:
        if game_state.phase != "point":
            return []

        # 🔍 Check if the player already has Place bets
        existing_place_bets = [
            b for b in table.bets
            if b.owner == player and b.bet_type == "Place" and b.number in self.inside_numbers and b.status != "removed"
        ]
        if existing_place_bets:
            return []

        bets: List[Bet] = []
        unit = self.unit_levels[self.level] if self.mode == "regress" else self.unit_levels[-1]

        for number in self.inside_numbers:
            base_unit = RulesEngine.get_bet_unit("Place", number)
            bet_amount = base_unit * unit
            bet = RulesEngine.create_bet("Place", bet_amount, player, number)
            bets.append(bet)

        return bets

    def adjust_bets(self, game_state: GameState, player: Player, table: "Table") -> Optional[List[Bet]]:
        last_roll = game_state.stats.last_roll_total
        if last_roll not in self.inside_numbers:
            return None

        updated_bets: List[Bet] = []

        if self.mode == "regress":
            hit_bet = next(
                (
                    b for b in table.bets
                    if b.owner == player and b.bet_type == "Place" and b.number == last_roll and b.status == "won"
                ),
                None
            )
            if not hit_bet:
                return None

            # ✅ Determine regression level
            regression_index = max(0, min(self.hits, len(self.unit_levels) - 1))
            current_unit = self.unit_levels[regression_index]
            adjuster: BetAdjuster = RegressAdjuster(self.unit_levels, regression_index)

            # ✅ Regress *all* of the player’s inside Place bets
            for bet in table.bets:
                if bet.owner == player and bet.bet_type == "Place" and bet.number in self.inside_numbers:
                    bet.amount = current_unit * RulesEngine.get_bet_unit(bet.bet_type, bet.number)
                    adjuster.adjust(bet, table, table.rules_engine)
                    updated_bets.append(bet)

            table.play_by_play.write(f"  📉 {player.name} regressing to unit level {current_unit} after hit #{self.hits}")
            
            # 👇 Switch to press mode after completing regression
            if current_unit == self.low_unit:
                self.mode = "press"
                table.play_by_play.write(
                    f"  🎯 {player.name} completed regression to unit ${current_unit} — switching to press mode."
                )

        elif self.mode == "press":
            # ✅ Check BEFORE adjusting if we're over original exposure
            total_exposure = sum(
                bet.amount for bet in table.bets
                if bet.owner == player and bet.bet_type == "Place" and bet.number in self.inside_numbers
            )
            if total_exposure >= self.original_exposure:
                self.mode = "regress"
                self.level = 0
                self.hits = 0
                table.play_by_play.write(
                    f"  🛑 {player.name}'s total press goal of (${total_exposure}) met! — resetting to regression mode."
                )
                return None  # 🚫 Do not adjust this round — wait for next regression step

            # 👇 Only reach here if exposure is still below threshold
            half_press_adjuster = HalfPressAdjuster()
            for bet in table.bets:
                if (
                    bet.owner == player and bet.bet_type == "Place"
                    and bet.number == last_roll and bet.status == "won"
                ):
                    half_press_adjuster.adjust(bet, table, table.rules_engine)
                    updated_bets.append(bet)

        return updated_bets if updated_bets else None
    