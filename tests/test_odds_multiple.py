import unittest
from craps.rules_engine import RulesEngine
from craps.rules import ODDS_MULTIPLIERS

class TestRulesEngine(unittest.TestCase):
    """Unit tests for the RulesEngine, specifically testing odds multipliers."""

    def test_odds_multipliers(self):
        """Ensure that the correct odds multiplier is returned for each point number."""
        test_cases = [
            ("1x", 4, 1),
            ("1x", 6, 1),
            ("2x", 5, 2),
            ("2x", 9, 2),
            ("1x-2x-3x", 4, 1),
            ("1x-2x-3x", 5, 2),
            ("1x-2x-3x", 6, 3),
            ("3x-4x-5x", 4, 3),
            ("3x-4x-5x", 5, 4),
            ("3x-4x-5x", 6, 5),
            ("3x-4x-5x", 8, 5),
            ("3x-4x-5x", 9, 4),
            ("3x-4x-5x", 10, 3),
            ("10x", 4, 10),
            ("20x", 8, 20),
            ("100x", 10, 100),
            ("100x", 6, 100),
            ("100x", 9, 100),
        ]
        
        for odds_type, point, expected in test_cases:
            with self.subTest(odds_type=odds_type, point=point):
                self.assertEqual(RulesEngine.get_odds_multiplier(odds_type, point), expected)

    def test_invalid_odds_type(self):
        """Ensure that an invalid odds type raises a ValueError."""
        with self.assertRaises(ValueError):
            RulesEngine.get_odds_multiplier("InvalidOdds", 6)

    def test_none_point(self):
        """Ensure that passing None as the point returns None (no odds allowed)."""
        self.assertIsNone(RulesEngine.get_odds_multiplier("3x-4x-5x", None))
    
    def test_unknown_point(self):
        """Ensure that passing an unsupported point number returns None."""
        self.assertIsNone(RulesEngine.get_odds_multiplier("3x-4x-5x", 11))

    def test_flat_odds_multipliers(self):
        """Ensure flat multipliers return the correct value regardless of point number."""
        for odds_type, expected in [("10x", 10), ("20x", 20), ("100x", 100)]:
            with self.subTest(odds_type=odds_type):
                for point in [4, 5, 6, 8, 9, 10]:  # Test all possible points
                    self.assertEqual(RulesEngine.get_odds_multiplier(odds_type, point), expected)

if __name__ == "__main__":
    unittest.main()