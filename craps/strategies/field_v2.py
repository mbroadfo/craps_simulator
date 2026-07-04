from __future__ import annotations
from typing import Any, Tuple

from craps.strategy_contract import BetSpec, ContractStrategy, Layout, TableView


class FieldV2(ContractStrategy):
    """v2 port of FieldBetStrategy: keep one Field bet up in any phase."""

    name = "Field v2"

    def __init__(self, min_bet: int) -> None:
        self.min_bet = min_bet

    def wants(self, view: TableView, memo: Any) -> Tuple[Layout, Any]:
        if view.stage != "place" or view.has("Field"):
            return (), memo
        return (BetSpec("Field", self.min_bet),), memo
