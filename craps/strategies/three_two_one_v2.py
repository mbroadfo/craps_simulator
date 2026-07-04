from __future__ import annotations
from typing import Any, Dict, List, Tuple

from craps.rules import ODDS_MULTIPLIERS
from craps.strategy_contract import BetSpec, ContractStrategy, Layout, TableView, flat_bet_minimum


class ThreeTwoOneV2(ContractStrategy):
    """v2 port of ThreeTwoOneStrategy: pass line + odds + inside numbers,
    turning all place bets off after 3 hits (2 on a 4/10 point).

    ``turned_off`` is an instance attribute because CrapsEngine's
    refresh_bet_statuses reads it off the strategy object each roll — the
    adapter mirrors it. It is deterministic state, reset on come-out exactly
    as v1 does.
    """

    name = "Three-Two-One v2"

    def __init__(self, min_bet: int, odds_type: str = "2x") -> None:
        self.min_bet = min_bet
        self.odds_type = odds_type
        self.turned_off = False

    def _memo(self, memo: Any) -> Dict[str, int]:
        return memo if isinstance(memo, dict) else {"hits": 0}

    def wants(self, view: TableView, memo: Any) -> Tuple[Layout, Any]:
        memo = self._memo(memo)

        if view.stage == "place":
            if view.phase == "come-out":
                # v1 submits unconditionally; the table rejects duplicates
                return (BetSpec("Pass Line", self.min_bet),), memo

            specs: List[BetSpec] = []
            if not view.has("Pass Line Odds"):
                data = ODDS_MULTIPLIERS.get(self.odds_type)
                multiplier = 0
                if isinstance(data, dict):
                    multiplier = (data.get(view.point) if view.point is not None else None) or 0
                elif data:
                    multiplier = data
                for b in view.bets:
                    if b.bet_type == "Pass Line":
                        specs.append(BetSpec("Pass Line Odds", self.min_bet * multiplier, odds_on="Pass Line"))
            for num in (5, 6, 8, 9):
                if num == view.point:
                    continue
                existing = next((b for b in view.bets if b.bet_type == "Place" and b.number == num), None)
                if existing is None:
                    specs.append(BetSpec("Place", flat_bet_minimum(view.table_minimum, num), number=num))
                elif existing.status == "inactive":
                    specs.append(BetSpec("Place", existing.amount, number=num, set_status="active"))
            return tuple(specs), memo

        # Adjust stage
        if view.phase != "come-out" and view.point is None:
            return (), memo
        if view.phase == "come-out":
            self.turned_off = False
            return (), {"hits": 0}

        specs = []
        for b in view.bets:
            if b.bet_type == "Place" and b.status == "won":
                memo["hits"] += 1
                specs.append(BetSpec("Place", b.amount, number=b.number, set_status="active"))

        if not self.turned_off:
            threshold_met = (
                (view.point in (4, 10) and memo["hits"] >= 2)
                or (view.point in (5, 6, 8, 9) and memo["hits"] >= 3)
            )
            if threshold_met and any(b.bet_type == "Place" for b in view.bets):
                self.turned_off = True
                for b in view.bets:
                    if b.bet_type == "Place":
                        specs.append(BetSpec("Place", b.amount, number=b.number, set_status="inactive"))
        return tuple(specs), memo

    def new_shooter_memo(self, memo: Any) -> Any:
        return memo  # v1 resets via the come-out adjust branch, not on_new_shooter
