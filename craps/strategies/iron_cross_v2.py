from __future__ import annotations
from typing import Any, List, Optional, Tuple

from craps.rules import ODDS_MULTIPLIERS
from craps.strategy_contract import BetSpec, ContractStrategy, Layout, TableView


def _odds_multiplier(odds_type: str, point: Optional[int]) -> Optional[int]:
    """Pure lookup into the odds table (same data RulesEngine reads)."""
    data = ODDS_MULTIPLIERS.get(odds_type)
    if isinstance(data, dict):
        return data.get(point) if point is not None else None
    return data


def _place_amount(table_minimum: int, number: int) -> int:
    """Place-bet minimum per RulesEngine.get_minimum_bet: 6/8 bet in units of
    table_min + table_min//5 (e.g. $12 on a $10 table), others at table min."""
    if number in (6, 8):
        return table_minimum + (table_minimum // 5)
    return table_minimum


class IronCrossV2(ContractStrategy):
    """v2 port of IronCrossStrategy: pass line (+odds) with Place 5/6/8
    around the point and a perpetual Field bet during the point phase."""

    name = "Iron Cross v2"
    reactivates_place_bets = True

    def __init__(
        self,
        min_bet: int,
        play_pass_line: bool = True,
        odds_type: Optional[str] = None,
    ) -> None:
        self.min_bet = min_bet
        self.play_pass_line = play_pass_line
        self.odds_type = odds_type

    def wants(self, view: TableView, memo: Any) -> Tuple[Layout, Any]:
        specs: List[BetSpec] = []

        if view.phase == "come-out":
            if self.play_pass_line and not view.has("Pass Line"):
                specs.append(BetSpec("Pass Line", self.min_bet))
            return tuple(specs), memo

        # Point phase
        if self.play_pass_line and self.odds_type and not view.has("Pass Line Odds"):
            pass_line = view.get("Pass Line")
            if pass_line is not None:
                multiplier = _odds_multiplier(self.odds_type, view.point)
                if multiplier is not None:
                    odds_amount = min(pass_line.amount * multiplier, view.bankroll)
                    specs.append(BetSpec("Pass Line Odds", odds_amount, odds_on="Pass Line"))

        numbers = [n for n in (5, 6, 8) if n != view.point]
        for number in numbers:
            already_covered = any(
                b.bet_type.startswith("Place") and b.number == number
                for b in view.bets
            )
            if not already_covered:
                specs.append(BetSpec("Place", _place_amount(view.table_minimum, number), number=number))

        if not view.has("Field"):
            specs.append(BetSpec("Field", self.min_bet))

        return tuple(specs), memo
