from __future__ import annotations
from typing import Any, Tuple

from craps.strategy_contract import BetSpec, ContractStrategy, Layout, TableView


class PassLineV2(ContractStrategy):
    """v2 port of PassLineStrategy (flat, no odds).

    Note: v1 PassLineStrategy's odds path returns bets from adjust_bets,
    which the engine discards — so the observed v1 behavior is flat pass
    line only. That quirk is flagged in the PR; this port matches what
    v1 actually does, not what it looks like it does.
    """

    name = "Pass Line v2"

    def __init__(self, bet_amount: int) -> None:
        self.bet_amount = bet_amount

    def wants(self, view: TableView, memo: Any) -> Tuple[Layout, Any]:
        if view.phase == "come-out" and not view.has("Pass Line"):
            return (BetSpec("Pass Line", self.bet_amount),), memo
        return (), memo
