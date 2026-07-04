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
from craps.strategies.field_strategy import FieldBetStrategy
from craps.strategies.place_strategy import PlaceBetStrategy
from craps.strategies.lay_strategy import LayBetStrategy
from craps.strategies.pass_line_odds_strategy import PassLineOddsStrategy
from craps.strategies.double_hop_strategy import DoubleHopStrategy
from craps.strategies.hardway_highway_strategy import HardwayHighwayStrategy
from craps.strategies.all_tall_small_strategy import AllTallSmallStrategy
from craps.strategies.three_point_molly_strategy import ThreePointMollyStrategy
from craps.strategies.three_point_dolly_strategy import ThreePointDollyStrategy
from craps.strategies.three_two_one_strategy import ThreeTwoOneStrategy
from craps.strategies.regress_then_press_strategy import RegressThenPressStrategy
from craps.strategies.place_reggression_strategy import PlaceRegressionStrategy
from craps.bet_adjusters import PressStyle
from craps.strategies.pass_line_v2 import PassLineV2
from craps.strategies.iron_cross_v2 import IronCrossV2
from craps.strategies.field_v2 import FieldV2
from craps.strategies.place_v2 import PlaceV2
from craps.strategies.lay_v2 import LayV2
from craps.strategies.pass_line_odds_v2 import PassLineOddsV2
from craps.strategies.double_hop_v2 import DoubleHopV2
from craps.strategies.hardway_highway_v2 import HardwayHighwayV2
from craps.strategies.all_tall_small_v2 import AllTallSmallV2
from craps.strategies.three_point_v2 import ThreePointMollyV2, ThreePointDollyV2
from craps.strategies.three_two_one_v2 import ThreeTwoOneV2
from craps.strategies.regress_press_v2 import RegressPressV2
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


# Each entry: name -> (v1 factory, v2 factory), mirroring the lineup configs.
STRATEGY_PAIRS = {
    "PassLine": (old_pass_line, new_pass_line),
    "IronCross": (old_iron_cross, new_iron_cross),
    "Field": (
        lambda e: FieldBetStrategy(min_bet=MIN_BET),
        lambda e: V2StrategyAdapter(FieldV2(min_bet=MIN_BET)),
    ),
    "Inside": (
        lambda e: PlaceBetStrategy(table=None, rules_engine=e.rules_engine, numbers_or_strategy="inside"),
        lambda e: V2StrategyAdapter(PlaceV2("inside")),
    ),
    "Across": (
        lambda e: PlaceBetStrategy(table=None, rules_engine=e.rules_engine, numbers_or_strategy="across"),
        lambda e: V2StrategyAdapter(PlaceV2("across")),
    ),
    "Place68": (
        lambda e: PlaceBetStrategy(table=None, rules_engine=e.rules_engine, numbers_or_strategy=[6, 8]),
        lambda e: V2StrategyAdapter(PlaceV2([6, 8])),
    ),
    "LayOutside": (
        lambda e: LayBetStrategy(table=None, rules_engine=e.rules_engine, numbers_or_strategy="Outside"),
        lambda e: V2StrategyAdapter(LayV2("Outside")),
    ),
    "PassLineOdds1x": (
        lambda e: PassLineOddsStrategy(table=None, rules_engine=e.rules_engine, odds_multiple="1x"),
        lambda e: V2StrategyAdapter(PassLineOddsV2(odds_multiple="1x")),
    ),
    "DoubleHop": (
        lambda e: DoubleHopStrategy(base_bet=1, hop_target=(3, 3), rules_engine=e.rules_engine),
        lambda e: V2StrategyAdapter(DoubleHopV2(hop_target=(3, 3), base_bet=1)),
    ),
    "HardwayHighway": (
        lambda e: HardwayHighwayStrategy(table=None, rules_engine=e.rules_engine, play_by_play=e.play_by_play),
        lambda e: V2StrategyAdapter(HardwayHighwayV2()),
    ),
    "AllTallSmall": (
        lambda e: AllTallSmallStrategy(table=None, rules_engine=e.rules_engine, play_by_play=e.play_by_play,
                                       ats_type="AllTallSmall", bet_amount=15),
        lambda e: V2StrategyAdapter(AllTallSmallV2(ats_type="AllTallSmall", bet_amount=15)),
    ),
    "ThreePointMolly": (
        lambda e: ThreePointMollyStrategy(table=None, bet_amount=MIN_BET, odds_type="3x-4x-5x"),
        lambda e: V2StrategyAdapter(ThreePointMollyV2(bet_amount=MIN_BET, odds_type="3x-4x-5x")),
    ),
    "ThreePointDolly": (
        lambda e: ThreePointDollyStrategy(table=None, bet_amount=MIN_BET, odds_type="3x-4x-5x"),
        lambda e: V2StrategyAdapter(ThreePointDollyV2(bet_amount=MIN_BET, odds_type="3x-4x-5x")),
    ),
    "ThreeTwoOne": (
        lambda e: ThreeTwoOneStrategy(rules_engine=e.rules_engine, min_bet=MIN_BET, odds_type="1x"),
        lambda e: V2StrategyAdapter(ThreeTwoOneV2(min_bet=MIN_BET, odds_type="1x")),
    ),
    "RegressHalfPress": (
        lambda e: RegressThenPressStrategy(
            regression_strategy=PlaceRegressionStrategy(high_unit=10, low_unit=3, regression_factor=2, regress_units=5),
            press_style=PressStyle.HALF,
        ),
        lambda e: V2StrategyAdapter(RegressPressV2(high_unit=10, low_unit=3, regression_factor=2, regress_units=5)),
    ),
}


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

    def test_parity_all_ported_strategies(self):
        for name, (old_factory, new_factory) in STRATEGY_PAIRS.items():
            with self.subTest(strategy=name):
                self.assert_parity(old_factory, new_factory)


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
