from __future__ import annotations
from typing import Any, List, Tuple, Union

from craps.strategy_contract import BetSpec, ContractStrategy, Layout, TableView, flat_bet_minimum

_GROUPS = {
    "inside": [5, 6, 8, 9],
    "across": [4, 5, 6, 8, 9, 10],
}


class PlaceV2(ContractStrategy):
    """v2 port of PlaceBetStrategy: cover a number group with Place bets
    during the point phase, skipping numbers already covered by the player's
    Pass Line point or an existing Place bet."""

    name = "Place v2"

    def __init__(self, numbers_or_strategy: Union[str, List[int]]) -> None:
        if isinstance(numbers_or_strategy, str):
            if numbers_or_strategy not in _GROUPS:
                raise ValueError(f"Invalid strategy: {numbers_or_strategy}")
            self.numbers = _GROUPS[numbers_or_strategy]
        else:
            self.numbers = numbers_or_strategy

    def wants(self, view: TableView, memo: Any) -> Tuple[Layout, Any]:
        if view.stage != "place" or view.phase != "point":
            return (), memo

        specs = []
        for number in self.numbers:
            covered = any(
                (b.bet_type == "Pass Line" and view.point == number)
                or (b.bet_type.startswith("Place") and b.number == number)
                for b in view.bets
            )
            if not covered:
                specs.append(BetSpec("Place", flat_bet_minimum(view.table_minimum, number), number=number))
        return tuple(specs), memo
