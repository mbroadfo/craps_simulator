import unittest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import HOUSE_RULES, DICE_TEST_PATTERNS
from craps.craps_engine import CrapsEngine
from craps.events import (
    Event,
    SessionStarted,
    ShooterAssigned,
    BetPlaced,
    DiceRolled,
    BetResolved,
    PointEstablished,
    PointHit,
    SevenOut,
)


class TestEngineEvents(unittest.TestCase):
    """The engine must emit the event stream in parallel with existing behavior."""

    def _run_pattern(self, pattern, num_shooters=2):
        engine = CrapsEngine(quiet_mode=True)
        recorded = []
        engine.events.subscribe(Event, recorded.append)

        self.assertTrue(engine.setup_session(
            house_rules_dict=HOUSE_RULES,
            num_shooters=num_shooters,
            dice_mode="live",
        ))
        self.assertGreater(engine.add_players_from_config(), 0)
        engine.lock_session()
        engine.assign_next_shooter()

        engine.dice.forced_rolls.extend(pattern)
        for _ in pattern:
            engine.accept_bets()
            outcome = engine.roll_dice()
            prev_phase = engine.game_state.phase
            engine.resolve_bets(outcome)
            engine.refresh_bet_statuses()
            engine.handle_post_roll(outcome, prev_phase)

        return recorded

    def _of_type(self, recorded, *event_types):
        return [e for e in recorded if isinstance(e, event_types)]

    def test_point_then_seven_out_sequence(self):
        recorded = self._run_pattern(DICE_TEST_PATTERNS["point_7_out"])

        flow = self._of_type(
            recorded, SessionStarted, ShooterAssigned, PointEstablished, PointHit, SevenOut
        )
        self.assertIsInstance(flow[0], SessionStarted)
        self.assertEqual(flow[0].num_shooters, 2)
        self.assertIsInstance(flow[1], ShooterAssigned)
        self.assertEqual(flow[1].shooter_index, 1)
        self.assertEqual(flow[2], PointEstablished(point=6))
        self.assertEqual(flow[3], SevenOut(shooter_index=1))
        # Seven-out hands the dice to the next shooter
        self.assertIsInstance(flow[4], ShooterAssigned)
        self.assertEqual(flow[4].shooter_index, 2)
        self.assertEqual(len(flow), 5)

    def test_point_hit_sequence(self):
        recorded = self._run_pattern(DICE_TEST_PATTERNS["point_hit"])

        flow = self._of_type(recorded, PointEstablished, PointHit, SevenOut)
        self.assertEqual(flow, [PointEstablished(point=6), PointHit(point=6)])

    def test_dice_rolled_events_match_forced_rolls(self):
        pattern = DICE_TEST_PATTERNS["point_7_out"]
        recorded = self._run_pattern(pattern)

        rolls = self._of_type(recorded, DiceRolled)
        self.assertEqual([r.dice for r in rolls], pattern)
        self.assertEqual([r.total for r in rolls], [sum(d) for d in pattern])
        self.assertEqual([r.roll_number for r in rolls], [1, 2, 3])
        # Phase captured at roll time: come-out, then point until the 7-out resolves
        self.assertEqual(rolls[0].phase, "come-out")
        self.assertEqual(rolls[1].phase, "point")
        self.assertEqual(rolls[1].point, 6)

    def test_bet_events_are_emitted(self):
        recorded = self._run_pattern(DICE_TEST_PATTERNS["point_7_out"])

        placed = self._of_type(recorded, BetPlaced)
        resolved = self._of_type(recorded, BetResolved)
        self.assertGreater(len(placed), 0, "No BetPlaced events emitted")
        self.assertGreater(len(resolved), 0, "No BetResolved events emitted")
        for event in resolved:
            # Both "push" and "pushed" exist in the current bet vocabulary
            self.assertIn(event.status, ("won", "lost", "pushed", "push"))

    def test_subscribe_by_concrete_type(self):
        engine = CrapsEngine(quiet_mode=True)
        started = []
        engine.events.subscribe(SessionStarted, started.append)
        self.assertTrue(engine.setup_session(house_rules_dict=HOUSE_RULES, num_shooters=1))
        self.assertEqual(started, [SessionStarted(num_shooters=1)])


if __name__ == "__main__":
    unittest.main()
