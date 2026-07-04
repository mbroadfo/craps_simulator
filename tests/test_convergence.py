"""House-edge convergence: ~1M seeded rolls per strategy vs theoretical edge.

Excluded from the default pytest run (see pyproject addopts) — run with:

    pytest -m convergence -q

Seeded dice make each check deterministic: this guards against payout-math
regressions, anchored near theory, rather than being a statistical coin flip.
Edge is computed from the bankroll delta over total amount bet, which is
robust to the stats ledger's stake-inclusive accounting for contract bets.
"""
import unittest
import sys
import os

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import HOUSE_RULES
from craps.craps_engine import CrapsEngine
from craps.player import Player
from craps.strategies.pass_line_v2 import PassLineV2
from craps.strategies.field_v2 import FieldV2
from craps.strategies.place_v2 import PlaceV2
from craps.strategy_contract import V2StrategyAdapter

SEED = 20260704
NUM_SHOOTERS = 120_000  # ~8.5 rolls/shooter → ~1M rolls
BANKROLL = 50_000_000   # deep enough that bets never get rejected for funds


def run_convergence_session(contract):
    engine = CrapsEngine(quiet_mode=True)
    assert engine.setup_session(
        house_rules_dict=HOUSE_RULES,
        num_shooters=NUM_SHOOTERS,
        dice_mode="live",
        dice_seed=SEED,
    )
    player = Player(name="Grinder", strategy_name="Grinder", initial_balance=BANKROLL)
    player.betting_strategy = V2StrategyAdapter(contract)
    engine.player_lineup.add_player(player)
    engine.stats.initialize_player_stats([player])
    engine.stats.num_players = 1
    engine.lock_session()
    engine.assign_next_shooter()

    for _ in range(NUM_SHOOTERS):
        while True:
            engine.accept_bets()
            outcome = engine.roll_dice()
            prev_phase = engine.game_state.phase
            engine.resolve_bets(outcome)
            engine.refresh_bet_statuses()
            summary = engine.handle_post_roll(outcome, prev_phase)
            if summary.new_shooter_assigned:
                break

    total_bet = engine.stats.total_amount_bet
    net = player.balance - BANKROLL
    edge_pct = (-net / total_bet) * 100 if total_bet else 0.0
    return edge_pct, engine.stats.session_rolls, total_bet


@pytest.mark.convergence
class TestHouseEdgeConvergence(unittest.TestCase):

    def check(self, contract, expected_edge, tolerance):
        edge, rolls, total_bet = run_convergence_session(contract)
        self.assertGreater(rolls, 900_000, "Session too short for convergence")
        self.assertAlmostEqual(
            edge, expected_edge, delta=tolerance,
            msg=(
                f"{contract.name}: realized edge {edge:.3f}% vs theoretical "
                f"{expected_edge}% ±{tolerance} over {rolls:,} rolls (${total_bet:,} bet)"
            ),
        )

    def test_pass_line_edge(self):
        self.check(PassLineV2(bet_amount=10), expected_edge=1.41, tolerance=0.15)

    def test_field_edge(self):
        # 2:1 on the 2 and 3:1 on the 12 per HOUSE_RULES → 2.78%
        self.check(FieldV2(min_bet=10), expected_edge=2.78, tolerance=0.20)

    def test_place_six_eight_edge(self):
        self.check(PlaceV2([6, 8]), expected_edge=1.52, tolerance=0.15)


if __name__ == "__main__":
    unittest.main()
