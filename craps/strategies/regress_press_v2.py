from __future__ import annotations
from typing import Any, Dict, List, Tuple

from craps.strategy_contract import BetSpec, ContractStrategy, Layout, TableView


def _place_unit(number: int) -> int:
    """RulesEngine.get_bet_unit for Place: $6 units on 6/8, $5 on 4/5/9/10."""
    return 6 if number in (6, 8) else 5


def _fresh_memo() -> Dict[str, Any]:
    return {"mode": "regress", "hits": 0}


class RegressPressV2(ContractStrategy):
    """v2 port of the RegressHalfPress lineup entry.

    Fidelity: v1's RegressThenPressStrategy never activates its composite
    press mode — ``transitioned`` is never set True — so observed behavior is
    the inner PlaceRegressionStrategy alone (which has its own internal
    regress/press cycle). This port implements exactly that.
    """

    name = "Regress Press v2"

    def __init__(
        self,
        high_unit: int = 10,
        low_unit: int = 2,
        regression_factor: int = 2,
        regress_units: int = 10,
    ) -> None:
        self.high_unit = high_unit
        self.low_unit = low_unit
        self.regression_factor = regression_factor
        self.regress_units = regress_units
        self.unit_levels = self._generate_unit_levels()
        self.inside_numbers = {5, 6, 8, 9}

    def _generate_unit_levels(self) -> List[int]:
        levels = [self.high_unit]
        while levels[-1] > self.low_unit:
            next_level = max(self.low_unit, levels[-1] // self.regression_factor)
            if next_level == levels[-1]:
                break
            levels.append(next_level)
        return levels

    def new_shooter_memo(self, memo: Any) -> Any:
        return _fresh_memo()

    def wants(self, view: TableView, memo: Any) -> Tuple[Layout, Any]:
        if memo is None:
            memo = _fresh_memo()

        if view.stage == "place":
            if view.phase != "point":
                return (), memo
            if any(
                b.bet_type == "Place" and b.number in self.inside_numbers and b.status != "removed"
                for b in view.bets
            ):
                return (), memo
            unit = self.unit_levels[0] if memo["mode"] == "regress" else self.unit_levels[-1]
            specs = [
                BetSpec("Place", _place_unit(number) * unit, number=number)
                for number in self.inside_numbers
            ]
            return tuple(specs), memo

        # Adjust stage
        last_roll = view.last_roll_total
        if last_roll not in self.inside_numbers:
            return (), memo

        # v1's notify_payout fires per won bet before adjust_bets runs
        memo["hits"] += sum(1 for b in view.bets if b.status == "won")

        inside_places = [
            b for b in view.bets
            if b.bet_type == "Place" and isinstance(b.number, int) and b.number in self.inside_numbers
        ]
        desired: Dict[int, int] = {}

        if memo["mode"] == "regress":
            hit = any(b.number == last_roll and b.status == "won" for b in inside_places)
            if not hit:
                return (), memo
            index = max(0, min(memo["hits"], len(self.unit_levels) - 1))
            current_unit = self.unit_levels[index]
            # RegressAdjuster(unit_levels, index): clamp to levels[index - 1]
            target_unit = self.unit_levels[min(index - 1, len(self.unit_levels) - 1)]
            effective = min(current_unit, target_unit)
            for b in inside_places:
                assert isinstance(b.number, int)
                desired[b.number] = effective * _place_unit(b.number)
            if current_unit == self.low_unit:
                memo["mode"] = "press"
                memo["hits"] = 0

        elif memo["mode"] == "press":
            for b in inside_places:
                assert isinstance(b.number, int)
                if b.number == last_roll and b.status == "won":
                    # PressAdjuster HALF: add (winnings // 2) // unit * unit
                    desired[b.number] = b.amount + ((b.payout // 2) // b.unit) * b.unit
            if self.regress_units:
                exposure = sum(
                    desired.get(b.number, b.amount)
                    for b in inside_places if isinstance(b.number, int)
                )
                if exposure >= self.regress_units * 22:
                    memo["mode"] = "regress"
                    memo["hits"] = 0
                    for b in inside_places:
                        assert isinstance(b.number, int)
                        desired[b.number] = _place_unit(b.number) * self.regress_units

        adjust_specs = tuple(
            BetSpec("Place", amount, number=number)
            for number, amount in desired.items()
        )
        return adjust_specs, memo
