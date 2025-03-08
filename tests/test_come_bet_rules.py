# File: .\tests\test_come_bet_rules.py

import unittest
from craps.common import CommonTableSetup  # Import the common setup

class TestComeBetRules(unittest.TestCase):
    def setUp(self):
        """Initialize the common table setup for testing."""
        self.common_setup = CommonTableSetup()

    def test_come_bet_resolution(self):
        """Test Come bet resolution during the point phase."""
        # Place a Come bet during the point phase
        come_bet = self.common_setup.place_bet("Come", 100, phase="point")

        # Simulate a roll of 6 to move the Come bet to number 6
        dice_outcome = [3, 3]  # Total of 6
        self.common_setup.simulate_roll(dice_outcome, phase="point")

        # Check that the Come bet has moved to number 6
        self.assertEqual(come_bet.number, 6, "Come bet should move to number 6")

        # Simulate a point roll of 6 (win)
        dice_outcome = [3, 3]  # Total of 6
        self.common_setup.simulate_roll(dice_outcome, phase="point")

        # Check that the Come bet is resolved as won
        self.assertEqual(come_bet.status, "won", "Come bet should win on 6")

    def test_come_odds_bet_resolution(self):
        """Test Come Odds bet resolution after the Come bet has moved to a number."""
        # Place a Come bet during the point phase
        come_bet = self.common_setup.place_bet("Come", 100, phase="point")

        # Simulate a roll of 6 to move the Come bet to number 6
        dice_outcome = [3, 3]  # Total of 6
        self.common_setup.simulate_roll(dice_outcome, phase="point")

        # Place a Come Odds bet linked to the Come bet
        come_odds_bet = self.common_setup.place_bet("Come Odds", 100, phase="point")

        # Simulate a point roll of 6 (win)
        dice_outcome = [3, 3]  # Total of 6
        self.common_setup.simulate_roll(dice_outcome, phase="point")

        # Check that the Come Odds bet is resolved as won
        self.assertEqual(come_odds_bet.status, "won", "Come Odds bet should win on 6")

    def test_come_odds_bet_cannot_be_placed_before_come_bet_moves(self):
        """Test that Come Odds bets cannot be placed before the Come bet moves to a number."""
        # Place a Come bet during the point phase
        come_bet = self.common_setup.place_bet("Come", 100, phase="point")

        # Attempt to place a Come Odds bet before the Come bet moves to a number
        with self.assertRaises(ValueError):
            self.common_setup.place_bet("Come Odds", 100, phase="point")

    def test_come_odds_bet_can_be_placed_after_come_bet_moves(self):
        """Test that Come Odds bets can be placed after the Come bet moves to a number."""
        # Place a Come bet during the point phase
        come_bet = self.common_setup.place_bet("Come", 100, phase="point")

        # Simulate a roll of 6 to move the Come bet to number 6
        dice_outcome = [3, 3]  # Total of 6
        self.common_setup.simulate_roll(dice_outcome, phase="point")

        # Place a Come Odds bet after the Come bet has moved to a number
        come_odds_bet = self.common_setup.place_bet("Come Odds", 100, phase="point")

        # Check that the Come Odds bet is placed successfully
        self.assertEqual(come_odds_bet.status, "active", "Come Odds bet should be active")

if __name__ == "__main__":
    unittest.main()