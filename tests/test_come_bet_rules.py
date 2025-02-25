# File: .\tests\test_come_bet_rules.py

import unittest
from craps.rules_engine import RulesEngine
from craps.bet import Bet  # Import the base Bet class

class TestComeBetRules(unittest.TestCase):
    def setUp(self):
        """Initialize a Come bet, Come Odds bet, and the RulesEngine for testing."""
        self.player_name = "Alice"
        self.bet_amount = 100
        self.rules_engine = RulesEngine()

        # Create a Come bet using the RulesEngine
        self.come_bet = self.rules_engine.create_bet(
            "Come",
            self.bet_amount,
            self.player_name
        )

        # Simulate a come-out roll of 6 to move the Come bet to number 6
        dice_outcome = [3, 3]  # Total of 6
        self.rules_engine.resolve_bet(self.come_bet, dice_outcome, "point", None)
        self.come_bet.number = 6  # Set the number for the Come bet

        # Create a Come Odds bet using the RulesEngine
        self.come_odds_bet = self.rules_engine.create_bet(
            "Come Odds",
            self.bet_amount,
            self.player_name,
            number=self.come_bet.number,  # Pass the number from the Come bet
            parent_bet=self.come_bet
        )

    def test_come_bet_resolution(self):
        """Test Come bet resolution during the point phase."""
        # Simulate a point roll of 6
        dice_outcome = [3, 3]  # Total of 6
        self.rules_engine.resolve_bet(self.come_bet, dice_outcome, "point", None)
        self.assertEqual(self.come_bet.status, "won", "Come bet should win on 6")

    def test_come_odds_bet_resolution(self):
        """Test Come Odds bet resolution after the Come bet has moved to a number."""
        # Simulate a point roll of 6
        dice_outcome = [3, 3]  # Total of 6
        self.rules_engine.resolve_bet(self.come_odds_bet, dice_outcome, "point", None)
        self.assertEqual(self.come_odds_bet.status, "won", "Come Odds bet should win on 6")

    def test_come_odds_bet_cannot_be_placed_before_come_bet_moves(self):
        """Test that Come Odds bets cannot be placed before the Come bet moves to a number."""
        # Create a new Come bet without moving it to a number
        come_bet = self.rules_engine.create_bet(
            "Come",
            self.bet_amount,
            self.player_name
        )

        # Attempt to create a Come Odds bet without a number
        with self.assertRaises(ValueError):
            self.rules_engine.create_bet(
                "Come Odds",
                self.bet_amount,
                self.player_name,
                parent_bet=come_bet
            )

    def test_come_odds_bet_can_be_placed_after_come_bet_moves(self):
        """Test that Come Odds bets can be placed after the Come bet moves to a number."""
        # Simulate a come-out roll of 6 to move the Come bet to number 6
        dice_outcome = [3, 3]  # Total of 6
        self.rules_engine.resolve_bet(self.come_bet, dice_outcome, "point", None)
        self.assertEqual(self.come_bet.number, 6, "Come bet should move to number 6")

        # Now, Come Odds bets should be allowed
        self.assertTrue(
            self.rules_engine.can_make_bet("Come Odds", "point", parent_bet=self.come_bet),
            "Come Odds bets should be allowed during the point phase after the Come bet moves to a number"
        )

if __name__ == "__main__":
    unittest.main()