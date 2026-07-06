"""D5 theoretical-edge table and EdgeTracker ledger.

Edge values are asserted as exact Fractions against the standard
published numbers (wizardofodds per-bet-resolved convention), so any
drift in the math is a hard failure, not a tolerance smudge.
"""
from fractions import Fraction

import pytest

from craps.edge import (
    EdgeTracker,
    p_all_before_seven,
    p_before_seven,
    theoretical_edge,
)
from craps.events import BetResolved, Event
from craps.house_rules import HouseRules
from craps.table_runner import TableRunner


class TestProbabilities:
    def test_classic_six_before_seven(self):
        assert p_before_seven(6) == Fraction(5, 11)
        assert p_before_seven(4) == Fraction(1, 3)

    def test_inclusion_exclusion_singleton_matches_direct(self):
        for number in (2, 3, 4, 5, 6, 8, 9, 10, 11, 12):
            assert p_all_before_seven([number]) == p_before_seven(number)

    def test_ats_probabilities_are_sane(self):
        p_small = p_all_before_seven((2, 3, 4, 5, 6))
        p_all = p_all_before_seven((2, 3, 4, 5, 6, 8, 9, 10, 11, 12))
        assert 0 < p_all < p_small < Fraction(1, 10)


class TestTheoreticalEdges:
    @pytest.mark.parametrize("bet_type,number,expected", [
        ("Pass Line", None, Fraction(7, 495)),        # 1.4141%
        ("Come", None, Fraction(7, 495)),
        ("Don't Pass", None, Fraction(27, 1980)),     # 1.3636%
        ("Pass Line Odds", 6, Fraction(0)),
        ("Come Odds", 4, Fraction(0)),
        ("Place", 6, Fraction(1, 66)),                # 1.515%
        ("Place", 8, Fraction(1, 66)),
        ("Place", 5, Fraction(1, 25)),                # 4.0%
        ("Place", 4, Fraction(1, 15)),                # 6.667%
        ("Buy", 4, Fraction(1, 60)),                  # 1.667% vig on win
        ("Lay", 4, Fraction(1, 60)),                  # 1.667% vig on win
        ("Field", None, Fraction(1, 36)),             # 2.78% (2x2, 3x12)
        ("Hardways", 8, Fraction(1, 11)),             # 9.09%
        ("Hardways", 10, Fraction(1, 9)),             # 11.11%
        ("Proposition", 7, Fraction(1, 6)),           # 16.67%
        ("Proposition", 2, Fraction(5, 36)),          # 13.89%
        ("Proposition", 11, Fraction(1, 9)),          # 11.11%
        ("Any Craps", None, Fraction(1, 9)),          # 11.11%
        ("Hop", (3, 4), Fraction(1, 9)),              # easy hop 15:1
        ("Hop", (3, 3), Fraction(5, 36)),             # pair hop 30:1
    ], ids=str)
    def test_standard_edges_exact(self, bet_type, number, expected):
        assert theoretical_edge(bet_type, number) == expected

    def test_field_edge_follows_house_rules(self):
        double_double = HouseRules({"field_bet_payout_2": 2, "field_bet_payout_12": 2})
        triple_triple = HouseRules({"field_bet_payout_2": 3, "field_bet_payout_12": 3})
        assert theoretical_edge("Field", None, double_double) == Fraction(2, 36)  # 5.56%
        assert theoretical_edge("Field", None, triple_triple) == Fraction(0)      # fair game

    def test_upfront_vig_costs_more_than_on_win(self):
        upfront = HouseRules({"vig_on_win": False})
        assert theoretical_edge("Buy", 4, upfront) == Fraction(1, 20)  # 5.0%
        assert theoretical_edge("Lay", 4, upfront) == Fraction(1, 40)  # 2.5%
        for number in (4, 5, 9, 10):
            for bet_type in ("Buy", "Lay"):
                assert theoretical_edge(bet_type, number, upfront) > \
                    theoretical_edge(bet_type, number)

    def test_ats_edges_are_house_positive(self):
        for bet_type in ("All", "Tall", "Small"):
            edge = theoretical_edge(bet_type)
            assert edge is not None and Fraction(1, 20) < edge < Fraction(1, 2)

    def test_untabulated_types_return_none(self):
        assert theoretical_edge("Don't Place", 6) is None
        assert theoretical_edge("Point 7", None) is None


class TestEdgeTracker:
    @pytest.fixture(scope="class")
    def session(self):
        runner = TableRunner(
            table_id="edge",
            players=[
                ("Molly", "3-Point Molly"),
                ("Fielder", "Field"),
                ("Layla", "Lay Outside"),
                ("Hardy", "HardwayHighway"),
            ],
            max_shooters=15,
            dice_seed=515,
        )
        tracker = EdgeTracker(lambda: runner.engine.house_rules)
        tracker.subscribe(runner.engine.events)
        captured = []
        runner.engine.events.subscribe(Event, captured.append)
        runner.run()
        return tracker, captured

    def test_ledger_identities_match_the_stream(self, session):
        tracker, captured = session
        wagered = {}
        pnl = {}
        for e in captured:
            if isinstance(e, BetResolved) and e.status in ("won", "lost"):
                wagered[e.player_name] = wagered.get(e.player_name, 0) + e.amount
                pnl[e.player_name] = pnl.get(e.player_name, 0) + (
                    e.payout if e.status == "won" else -e.amount
                )
        assert tracker.wagered == wagered
        assert tracker.pnl == pnl
        assert sum(wagered.values()) > 0

    def test_single_bet_strategy_gets_that_exact_benchmark(self, session):
        tracker, _ = session
        snap = tracker.snapshot()["Fielder"]
        assert snap["theoretical_edge_pct"] == pytest.approx(-100 / 36)
        assert snap["uncovered_wagered"] == 0

    def test_every_amount_is_covered_or_reported(self, session):
        tracker, _ = session
        for name, snap in tracker.snapshot().items():
            covered = tracker.covered.get(name, 0)
            assert covered + snap["uncovered_wagered"] == snap["wagered"]
            assert snap["edge_delta_pct"] == pytest.approx(
                snap["realized_edge_pct"] - snap["theoretical_edge_pct"]
            )
