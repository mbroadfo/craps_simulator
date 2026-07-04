from __future__ import annotations
from typing import Any, Optional, Tuple, Union

from craps.rules import ODDS_MULTIPLIERS
from craps.strategy_contract import BetSpec, ContractStrategy, Layout, TableView


class PassLineOddsV2(ContractStrategy):
    """v2 port of PassLineOddsStrategy: pass line on come-out, table-minimum
    based odds when the point is on.

    Fidelity notes vs v1: odds size off the *table minimum* (not the pass
    line amount) and are not capped by bankroll; the odds bet is ephemeral
    (swept each roll by settle_resolved_bets), so it re-places every
    point-phase roll exactly as v1 does.
    """

    name = "Pass Line Odds v2"

    def __init__(self, odds_multiple: Union[int, str] = 1) -> None:
        self.odds_multiple = odds_multiple

    def _odds_amount(self, view: TableView) -> Optional[int]:
        if isinstance(self.odds_multiple, str):
            if view.point is None:
                return None
            data = ODDS_MULTIPLIERS.get(self.odds_multiple)
            multiplier = data.get(view.point) if isinstance(data, dict) else data
            if multiplier is None:
                return None
            return view.table_minimum * multiplier
        return view.table_minimum * self.odds_multiple

    def wants(self, view: TableView, memo: Any) -> Tuple[Layout, Any]:
        if view.stage != "place":
            return (), memo

        if view.phase == "come-out":
            if view.has("Pass Line"):
                return (), memo
            return (BetSpec("Pass Line", view.table_minimum),), memo

        if view.phase == "point":
            if view.has("Pass Line Odds") or not view.has("Pass Line"):
                return (), memo
            amount = self._odds_amount(view)
            if amount is None:
                return (), memo
            return (BetSpec("Pass Line Odds", amount, odds_on="Pass Line"),), memo

        return (), memo
