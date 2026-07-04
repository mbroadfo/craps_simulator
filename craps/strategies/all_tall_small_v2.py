from __future__ import annotations
from typing import Any, List, Optional, Tuple

from craps.strategy_contract import BetSpec, ContractStrategy, Layout, TableView

ATS_TYPE_MAP = {
    "AllTallSmall": ["All", "Tall", "Small"],
    "TallSmall": ["Tall", "Small"],
    "All": ["All"],
    "Tall": ["Tall"],
    "Small": ["Small"],
}


class AllTallSmallV2(ContractStrategy):
    """v2 port of AllTallSmallStrategy: keep All/Tall/Small bonus bets up on
    come-out rolls, skipping any already completed this shooter."""

    name = "All Tall Small v2"

    def __init__(self, ats_type: str = "AllTallSmall", bet_amount: Optional[int] = None) -> None:
        self.components = ATS_TYPE_MAP[ats_type]
        self.bet_amount = bet_amount

    def wants(self, view: TableView, memo: Any) -> Tuple[Layout, Any]:
        if view.stage != "place" or view.phase != "come-out":
            return (), memo

        # v1 falls back to get_minimum_bet("All") == 1 when no amount is set
        amount = self.bet_amount or 1

        completed = {
            "All": view.all_completed,
            "Tall": view.tall_completed,
            "Small": view.small_completed,
        }
        specs: List[BetSpec] = []
        for ats_type in self.components:
            if completed[ats_type]:
                continue
            if not view.has(ats_type):
                specs.append(BetSpec(ats_type, amount))
        return tuple(specs), memo
