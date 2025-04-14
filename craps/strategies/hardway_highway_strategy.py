from __future__ import annotations
from typing import Optional, List, TYPE_CHECKING, Set, Tuple
from craps.base_strategy import BaseStrategy

if TYPE_CHECKING:
    from craps.table import Table
    from craps.rules_engine import RulesEngine
    from craps.game_state import GameState
    from craps.player import Player
    from craps.bet import Bet

class HardwayHighwayStrategy(BaseStrategy):

    def _unit(self, table: Table) -> int:
        return table.house_rules.table_minimum // 2
    """
    Implements the HardwayHighway strategy:
    - 2-unit Pass Line bet on come-out
    - 1-unit Hard 6 and 8 always working
    - Once point is set, Place 6 and 8 for 2 units
    - Soft hits press Place bets up to 6 units
    - Hard hits press Place bets and double Hardway bet to 2 units
    - Reset Hardway bet to 1 unit if lost
    - Reset all bet levels on new shooter
    """

    def __init__(self, table: Table, rules_engine: RulesEngine, play_by_play: Optional[object] = None, strategy_name: Optional[str] = None) -> None:
        super().__init__(strategy_name or "HardwayHighway")
        self.table = table
        self.rules_engine = rules_engine
        self.play_by_play = play_by_play

        self.place_levels: dict[int, int] = {6: 2, 8: 2}  # starts at 2 units
        self.hardway_units: dict[int, int] = {6: 1, 8: 1}  # starts at 1 unit
        self.max_place_units: int = 6
        self.max_hardway_units: int = 2

    def on_new_shooter(self) -> None:
        self.place_levels = {6: 2, 8: 2}
        self.hardway_units = {6: 1, 8: 1}

    def place_bets(self, game_state: GameState, player: Player, table: Table) -> List[Bet]:
        bets: List[Bet] = []

        # Come-out: Pass Line bet only
        if game_state.phase == "come-out":
            if not player.has_active_bet(table, "Pass Line"):
                bets.append(self.rules_engine.create_bet("Pass Line", 2 * self._unit(table), player))

        # Hardways (always working)
        for num in (6, 8):
            if not player.has_active_bet(table, "Hardways", num):
                amount = self.hardway_units.get(num, 1) * self._unit(table)
                bets.append(self.rules_engine.create_bet("Hardways", amount, player, number=num))

        # After point is set, place the 6/8 if not already
        if game_state.puck_on:
            for num in (6, 8):
                if not player.has_active_bet(table, "Place", num):
                    desired = self.place_levels.get(num, 2) * self._unit(table)
                    min_required = self.rules_engine.get_minimum_bet("Place", table, number=num)
                    amount = max(desired, min_required)
                    bets.append(self.rules_engine.create_bet("Place", amount, player, number=num))

        return bets

    def adjust_bets(self, game_state: GameState, player: Player, table: Table) -> Optional[List[Bet]]:
        die1, die2 = table.dice.values if hasattr(table, "dice") and hasattr(table.dice, "values") else (0, 0)
        total = die1 + die2
        is_hard_hit = die1 == die2 and total in (6, 8)

        for bet in table.bets:
            if bet.owner != player or not bet.is_resolved():
                continue

            if bet.bet_type == "Hardways" and bet.number in (6, 8):
                if isinstance(bet.number, int):
                    num = bet.number
                else:
                    continue
                if bet.status == "lost":
                    self.hardway_units[num] = 1
                elif bet.status == "won" and self.hardway_units[num] < self.max_hardway_units:
                    self.hardway_units[num] = self.max_hardway_units

            if bet.bet_type == "Place" and bet.number in (6, 8):
                if isinstance(bet.number, int):
                    num = bet.number
                else:
                    continue
                if bet.status == "won":
                    if is_hard_hit and self.hardway_units[num] < self.max_hardway_units:
                        self.hardway_units[num] = self.max_hardway_units
                    if self.place_levels[num] < self.max_place_units:
                        self.place_levels[num] += 1

        return None
