from __future__ import annotations
from typing import Any, Dict, List, Tuple

from craps.strategy_contract import BetSpec, ContractStrategy, Layout, TableView, flat_bet_minimum


def _fresh_memo() -> Dict[str, Dict[int, int]]:
    return {"place_levels": {6: 2, 8: 2}, "hardway_units": {6: 1, 8: 1}}


class HardwayHighwayV2(ContractStrategy):
    """v2 port of HardwayHighwayStrategy.

    Fidelity notes (v1 observed behavior is the spec):
    - v1 reads ``table.dice`` for hard-hit detection, but Table has no dice
      attribute in real sessions, so ``is_hard_hit`` is always False — the
      place-win → hardway-double path never fires. Ported as such.
    - The "reset hardways after loss" branch iterates table bets after
      settlement, when lost bets are already removed — replicating the same
      iteration over the same post-settlement snapshot preserves that.
    """

    name = "Hardway Highway v2"
    MAX_PLACE_UNITS = 5
    MAX_HARDWAY_UNITS = 2

    def new_shooter_memo(self, memo: Any) -> Any:
        return _fresh_memo()

    def wants(self, view: TableView, memo: Any) -> Tuple[Layout, Any]:
        if memo is None:
            memo = _fresh_memo()
        unit = view.table_minimum // 2

        if view.stage == "place":
            specs: List[BetSpec] = []
            if view.phase == "come-out" and not view.has("Pass Line"):
                specs.append(BetSpec("Pass Line", 2 * unit))
            for num in (6, 8):
                if not view.has("Hardways", num):
                    specs.append(BetSpec("Hardways", memo["hardway_units"][num] * unit, number=num))
            if view.puck_on:
                for num in (6, 8):
                    if not view.has("Place", num):
                        desired = memo["place_levels"][num] * unit
                        amount = max(desired, flat_bet_minimum(view.table_minimum, num))
                        specs.append(BetSpec("Place", amount, number=num))
            return tuple(specs), memo

        # Adjust stage — is_hard_hit is always False in v1 (see class docstring)
        for b in view.bets:
            if b.bet_type == "Hardways" and isinstance(b.number, int) and b.number in (6, 8):
                if b.status == "won" and memo["hardway_units"][b.number] < self.MAX_HARDWAY_UNITS:
                    for target in (6, 8):
                        if memo["hardway_units"][target] < self.MAX_HARDWAY_UNITS:
                            memo["hardway_units"][target] = self.MAX_HARDWAY_UNITS
            if b.bet_type == "Place" and isinstance(b.number, int) and b.number in (6, 8):
                if b.status == "won":
                    memo["place_levels"][b.number] = min(
                        memo["place_levels"][b.number] + 1, self.MAX_PLACE_UNITS
                    )

        specs = []
        for b in view.bets:
            if b.bet_type == "Place" and isinstance(b.number, int) and b.number in (6, 8) and b.status == "won":
                unit_count = b.amount // b.unit
                desired_units = min(unit_count + 1, self.MAX_PLACE_UNITS)
                specs.append(BetSpec("Place", desired_units * b.unit, number=b.number))
        return tuple(specs), memo
