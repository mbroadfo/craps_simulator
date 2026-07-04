from __future__ import annotations
from typing import Any, Tuple

from craps.strategy_contract import BetSpec, ContractStrategy, Layout, TableView


class DoubleHopV2(ContractStrategy):
    """v2 port of DoubleHopStrategy: a perpetual hop bet, full-pressed after
    its first win and reset to the base amount after the second.

    Fidelity: v1 submits the hop bet every call unconditionally and relies on
    the table's duplicate rejection when one is already up — we do the same.
    """

    name = "Double Hop v2"

    def __init__(self, hop_target: Tuple[int, int], base_bet: int) -> None:
        self.hop_target = hop_target
        self.base_bet = base_bet

    def wants(self, view: TableView, memo: Any) -> Tuple[Layout, Any]:
        if view.stage == "place":
            return (BetSpec("Hop", self.base_bet, number=self.hop_target),), memo

        # Adjust stage: full-press on first hit, reset on second.
        specs = []
        for b in view.bets:
            if b.bet_type == "Hop" and b.number == self.hop_target and b.status == "won":
                if b.hits == 1:
                    # PressAdjuster FULL: add (winnings // unit) * unit
                    additional = (b.payout // b.unit) * b.unit
                    specs.append(BetSpec("Hop", b.amount + additional, number=self.hop_target))
                elif b.hits >= 2:
                    specs.append(BetSpec("Hop", self.base_bet, number=self.hop_target))
        return tuple(specs), memo
