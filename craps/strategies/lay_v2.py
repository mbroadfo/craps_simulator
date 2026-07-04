from __future__ import annotations
from typing import Any, List, Tuple, Union

from craps.strategy_contract import BetSpec, ContractStrategy, Layout, TableView, flat_bet_minimum

_GROUPS = {
    "outside": [4, 10],
    "inside": [5, 6, 8, 9],
    "across": [4, 5, 6, 8, 9, 10],
}


class LayV2(ContractStrategy):
    """v2 port of LayBetStrategy: lay against a number group during the
    point phase. v1 dedups on *active* lay bets specifically, so we do too."""

    name = "Lay v2"

    def __init__(self, numbers_or_strategy: Union[str, List[int]]) -> None:
        if isinstance(numbers_or_strategy, str):
            group = numbers_or_strategy.lower()
            if group not in _GROUPS:
                raise ValueError(f"Invalid lay strategy: {group}")
            self.numbers = _GROUPS[group]
        else:
            self.numbers = numbers_or_strategy

    def wants(self, view: TableView, memo: Any) -> Tuple[Layout, Any]:
        if view.stage != "place" or view.phase != "point":
            return (), memo

        specs = []
        for number in self.numbers:
            already_active = any(
                b.bet_type == "Lay" and b.number == number and b.status == "active"
                for b in view.bets
            )
            if not already_active:
                specs.append(BetSpec("Lay", flat_bet_minimum(view.table_minimum, number), number=number))
        return tuple(specs), memo
