"""Regression harness: v2 strategy ports must be money-identical to v1.

Two engines run the same seeded dice; the only variable is the strategy
implementation. The gate is per-roll bankroll equality — play-by-play text
is explicitly NOT part of the contract.
"""
import unittest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import HOUSE_RULES
from craps.craps_engine import CrapsEngine
from craps.dice import Dice
from craps.player import Player
from craps.strategies.pass_line_strategy import PassLineStrategy
from craps.strategies.iron_cross_strategy import IronCrossStrategy
from craps.strategies.pass_line_v2 import PassLineV2
from craps.strategies.iron_cross_v2 import IronCrossV2
from craps.strategy_contract import V2StrategyAdapter

MIN_BET = HOUSE_RULES["table_minimum"]
SEEDS = range(10)
NUM_SHOOTERS = 50


def run_session(strategy_factory, seed, num_shooters=NUM_SHOOTERS):
    """Run one full seeded session; return the per-roll bankroll trace."""
    engine = CrapsEngine(quiet_mode=True)
    assert engine.setup_session(
        house_rules_dict=HOUSE_RULES,
        num_shooters=num_shooters,
        dice_mode="live",
        dice_seed=seed,
    )
    player = Player(name="Tester", strategy_name="Tester")
    player.betting_strategy = strategy_factory(engine)
    engine.player_lineup.add_player(player)
    engine.stats.initialize_player_stats([player])
    engine.stats.num_players = 1
    engine.lock_session()
    engine.assign_next_shooter()

    bankrolls = []
    for _ in range(num_shooters):
        while True:
            engine.accept_bets()
            outcome = engine.roll_dice()
            prev_phase = engine.game_state.phase
            engine.resolve_bets(outcome)
            engine.refresh_bet_statuses()
            summary = engine.handle_post_roll(outcome, prev_phase)
            bankrolls.append(player.balance)
            if summary.new_shooter_assigned:
                break
    return bankrolls


def old_pass_line(engine):
    return PassLineStrategy(bet_amount=MIN_BET, table=None)


def new_pass_line(engine):
    return V2StrategyAdapter(PassLineV2(bet_amount=MIN_BET))


def old_iron_cross(engine):
    return IronCrossStrategy(
        table=None,
        rules_engine=engine.rules_engine,
        min_bet=MIN_BET,
        play_by_play=engine.play_by_play,
        play_pass_line=True,
        odds_type="3x-4x-5x",
    )


def new_iron_cross(engine):
    return V2StrategyAdapter(IronCrossV2(min_bet=MIN_BET, play_pass_line=True, odds_type="3x-4x-5x"))


class TestV2RegressionParity(unittest.TestCase):

    def assert_parity(self, old_factory, new_factory):
        total_rolls = 0
        for seed in SEEDS:
            with self.subTest(seed=seed):
                old_trace = run_session(old_factory, seed)
                new_trace = run_session(new_factory, seed)
                self.assertEqual(len(old_trace), len(new_trace),
                                 f"Roll counts diverged (seed={seed})")
                for roll, (old_b, new_b) in enumerate(zip(old_trace, new_trace), start=1):
                    self.assertEqual(
                        old_b, new_b,
                        f"Bankroll diverged at roll {roll} (seed={seed}): v1=${old_b} v2=${new_b}",
                    )
                total_rolls += len(old_trace)
        self.assertGreater(total_rolls, 2000, "Harness did not exercise enough rolls")

    def test_pass_line_parity(self):
        self.assert_parity(old_pass_line, new_pass_line)

    def test_iron_cross_parity(self):
        self.assert_parity(old_iron_cross, new_iron_cross)


class TestSeededDice(unittest.TestCase):

    def test_same_seed_same_sequence(self):
        a = Dice(seed=99)
        b = Dice(seed=99)
        self.assertEqual([a.roll() for _ in range(100)], [b.roll() for _ in range(100)])

    def test_different_seeds_diverge(self):
        a = Dice(seed=1)
        b = Dice(seed=2)
        self.assertNotEqual([a.roll() for _ in range(50)], [b.roll() for _ in range(50)])

    def test_unseeded_dice_still_roll(self):
        d = Dice()
        r = d.roll()
        self.assertTrue(1 <= r[0] <= 6 and 1 <= r[1] <= 6)

    def test_same_seed_same_session_bankrolls(self):
        first = run_session(new_iron_cross, seed=1234, num_shooters=10)
        second = run_session(new_iron_cross, seed=1234, num_shooters=10)
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
