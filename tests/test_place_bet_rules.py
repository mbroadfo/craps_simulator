# File: .\tests\test_place_bet_rules.py

import unittest
from craps.rules_engine import RulesEngine
from craps.bets.place_bet import PlaceBet

class TestPlaceBetRules(unittest.TestCase):
    def setUp(self):
        """Initialize a Place bet and the RulesEngine for testing."""
        self.player_name = "Alice"
        self.bet_amount = 100
        self.place_bet = PlaceBet(self.bet_amount, self.player_name, number=6)  # Place bet on 6
        self.rules_engine = RulesEngine()

    def test_point_phase(self):
        """Test Place bet behavior during the point phase."""
        # Test winning roll (6)
        dice_outcome = [3, 3]  # Total of 6
        self.rules_engine.resolve_bet(self.place_bet, dice_outcome, "point", None)
        self.assertEqual(self.place_bet.status, "won", "Place bet should win on 6")

        # Reset the bet for the next test
        self.place_bet = PlaceBet(self.bet_amount, self.player_name, number=6)

        # Test losing roll (7)
        dice_outcome = [3, 4]  # Total of 7
        self.rules_engine.resolve_bet(self.place_bet, dice_outcome, "point", None)
        self.assertEqual(self.place_bet.status, "lost", "Place bet should lose on 7")

        # Reset the bet for the next test
        self.place_bet = PlaceBet(self.bet_amount, self.player_name, number=6)

        # Test non-resolving roll (8)
        dice_outcome = [4, 4]  # Total of 8
        self.rules_engine.resolve_bet(self.place_bet, dice_outcome, "point", None)
        self.assertEqual(self.place_bet.status, "active", "Place bet should remain active on 8")

if __name__ == "__main__":
    unittest.main()