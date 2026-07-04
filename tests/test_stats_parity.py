"""Stats-parity gate for the event-consumer refactor (Phase 1, Step 4a).

Golden snapshots were generated from the pre-refactor engine (direct stats
calls). The refactored engine must reproduce every Statistics field
value-for-value on the same seeded dice. Regenerate goldens ONLY when a
behavior change is intentional and approved:

    python -m tests.test_stats_parity --regenerate
"""
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import HOUSE_RULES
from craps.craps_engine import CrapsEngine
from craps.player import Player
from craps.strategies.pass_line_strategy import PassLineStrategy
from craps.strategies.iron_cross_strategy import IronCrossStrategy
from craps.strategies.field_strategy import FieldBetStrategy

GOLDEN_DIR = os.path.join(os.path.dirname(__file__), "goldens")
SEEDS = [11, 42]
NUM_SHOOTERS = 30


def run_multiplayer_session(seed):
    engine = CrapsEngine(quiet_mode=True)
    assert engine.setup_session(
        house_rules_dict=HOUSE_RULES,
        num_shooters=NUM_SHOOTERS,
        dice_mode="live",
        dice_seed=seed,
    )
    players = [
        Player(name="Linus", strategy_name="Pass-Line"),
        Player(name="Crosstopher", strategy_name="Iron Cross"),
        Player(name="Fielder", strategy_name="Field"),
    ]
    players[0].betting_strategy = PassLineStrategy(bet_amount=10, table=None)
    players[1].betting_strategy = IronCrossStrategy(
        table=None, rules_engine=engine.rules_engine, min_bet=10,
        play_by_play=engine.play_by_play, play_pass_line=True, odds_type="3x-4x-5x",
    )
    players[2].betting_strategy = FieldBetStrategy(min_bet=10)
    for p in players:
        engine.player_lineup.add_player(p)
    engine.stats.initialize_player_stats(players)
    engine.stats.num_players = len(players)
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
    return engine


def snapshot(engine):
    """JSON-able snapshot of every Statistics field the session populates."""
    s = engine.stats
    return {
        "session_rolls": s.session_rolls,
        "total_amount_bet": s.total_amount_bet,
        "total_amount_won": s.total_amount_won,
        "total_amount_lost": s.total_amount_lost,
        "session_highest_bankroll": s.session_highest_bankroll,
        "session_lowest_bankroll": s.session_lowest_bankroll,
        "player_bankrolls": s.player_bankrolls,
        "highest_bankroll": s.highest_bankroll,
        "lowest_bankroll": s.lowest_bankroll,
        "max_table_risk": s.max_table_risk,
        "total_sevens": s.total_sevens,
        "shooter_stats": {str(k): v for k, v in s.shooter_stats.items()},
        "player_stats": s.player_stats,
        "roll_numbers": s.roll_numbers,
        "bankroll_history": s.bankroll_history,
        "at_risk_history": s.at_risk_history,
        "seven_out_rolls": s.seven_out_rolls,
        "point_number_rolls": s.point_number_rolls,
        "house_edge": s.house_edge(),
        "roll_history": engine.roll_history,
    }


def golden_path(seed):
    return os.path.join(GOLDEN_DIR, f"stats_seed{seed}.json")


class TestStatsParity(unittest.TestCase):

    def test_stats_match_golden(self):
        for seed in SEEDS:
            with self.subTest(seed=seed):
                with open(golden_path(seed), encoding="utf-8") as f:
                    golden = json.load(f)
                actual = json.loads(json.dumps(snapshot(run_multiplayer_session(seed))))
                for key in golden:
                    self.assertEqual(
                        golden[key], actual[key],
                        f"Statistics field '{key}' diverged from golden (seed={seed})",
                    )
                self.assertEqual(set(golden), set(actual))


if __name__ == "__main__":
    if "--regenerate" in sys.argv:
        os.makedirs(GOLDEN_DIR, exist_ok=True)
        for seed in SEEDS:
            with open(golden_path(seed), "w", encoding="utf-8") as f:
                json.dump(snapshot(run_multiplayer_session(seed)), f, indent=1)
            print(f"wrote {golden_path(seed)}")
    else:
        unittest.main()
