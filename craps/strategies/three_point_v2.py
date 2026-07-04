from __future__ import annotations
from typing import Any, List, Optional, Tuple

from craps.rules import ODDS_MULTIPLIERS
from craps.strategy_contract import BetSpec, ContractStrategy, Layout, TableView

_CONTRACT_LINE_TYPES = ("Pass Line", "Don't Pass")
_CONTRACT_COME_TYPES = ("Come", "Don't Come")


class _ThreePointBaseV2(ContractStrategy):
    """Shared v2 port for the 3-Point Molly (light side) and Dolly (dark
    side): line bet on come-out, up to two traveled come-family bets, and
    odds on every contract bet.

    Fidelity: odds bets are ephemeral (swept by settle_resolved_bets each
    roll), so odds re-place every point-phase roll at
    min(parent × multiplier, bankroll), exactly as v1's FreeOddsStrategy
    produces them. Odds specs carry the parent's number, which v1 assigns
    to the odds bet after creation.
    """

    line_type: str
    come_type: str

    def __init__(self, bet_amount: int, odds_type: Optional[str] = None) -> None:
        self.bet_amount = bet_amount
        self.odds_type = odds_type

    def _odds_specs(self, view: TableView) -> List[BetSpec]:
        assert self.odds_type is not None
        specs: List[BetSpec] = []
        data = ODDS_MULTIPLIERS.get(self.odds_type)
        for b in view.bets:
            if b.bet_type in _CONTRACT_LINE_TYPES:
                point_number = view.point
            elif b.bet_type in _CONTRACT_COME_TYPES:
                point_number = b.number if isinstance(b.number, int) else None
            else:
                continue
            if point_number is None:
                continue
            multiplier = data.get(point_number) if isinstance(data, dict) else data
            if multiplier is None:
                continue
            already = any(
                o.bet_type.endswith("Odds")
                and o.parent_type == b.bet_type
                and o.parent_number == b.number
                for o in view.bets
            )
            if already:
                continue
            amount = min(b.amount * multiplier, view.bankroll)
            specs.append(BetSpec(
                f"{b.bet_type} Odds", amount, number=b.number, odds_on=b.bet_type,
            ))
        return specs

    def wants(self, view: TableView, memo: Any) -> Tuple[Layout, Any]:
        if view.stage != "place":
            return (), memo

        specs: List[BetSpec] = []
        if view.phase == "come-out" and not view.has(self.line_type):
            specs.append(BetSpec(self.line_type, self.bet_amount))

        if view.phase == "point":
            traveled = [
                b for b in view.bets
                if b.bet_type == self.come_type and b.number is not None
            ]
            if len(traveled) < 2:
                specs.append(BetSpec(self.come_type, self.bet_amount))
            if self.odds_type:
                specs.extend(self._odds_specs(view))

        return tuple(specs), memo


class ThreePointMollyV2(_ThreePointBaseV2):
    name = "3-Point Molly v2"
    line_type = "Pass Line"
    come_type = "Come"


class ThreePointDollyV2(_ThreePointBaseV2):
    name = "3-Point Dolly v2"
    line_type = "Don't Pass"
    come_type = "Don't Come"
