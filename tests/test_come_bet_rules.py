import unittest
from craps.rules_engine import RulesEngine
from craps.bets.come_bet import ComeBet
from craps.bets.free_odds_bet import FreeOddsBet

class TestComeBetRules(unittest.TestCase):
    def setUp(self):
        """Initialize a Come bet, Come Odds bet, and the RulesEngine for testing."""
        self.player_name = "Alice"
        self.bet_amount = 100
        self.come_bet = ComeBet(self.bet_amount, self.player_name)
        self.come_odds_bet = FreeOddsBet("Come Odds", self.bet_amount, self.player_name, parent_bet=self.come_bet)
        self.rules_engine = RulesEngine()

    def test_come_bet_resolution(self):
        """Test Come bet resolution during the point phase."""
        # Simulate a come-out roll of 6
        dice_outcome = [3, 3]  # Total of 6
        self.rules_engine.resolve_bet(self.come_bet, dice_outcome, "point", None)
        self.assertEqual(self.come_bet.status, "active", "Come bet should remain active on 6")
        self.assertEqual(self.come_bet.number, 6, "Come bet should move to number 6")

        # Simulate a point roll of 6
        dice_outcome = [3, 3]  # Total of 6
        self.rules_engine.resolve_bet(self.come_bet, dice_outcome, "point", None)
        self.assertEqual(self.come_bet.status, "won", "Come bet should win on 6")

    def test_come_odds_bet_resolution(self):
        """Test Come Odds bet resolution after the Come bet has moved to a number."""
        # Simulate a come-out roll of 6 to move the Come bet to number 6
        dice_outcome = [3, 3]  # Total of 6
        self.rules_engine.resolve_bet(self.come_bet, dice_outcome, "point", None)
        self.assertEqual(self.come_bet.number, 6, "Come bet should move to number 6")

        # Place a Come Odds bet on number 6
        self.come_odds_bet.number = 6

        # Simulate a point roll of 6
        dice_outcome = [3, 3]  # Total of 6
        self.rules_engine.resolve_bet(self.come_odds_bet, dice_outcome, "point", None)
        self.assertEqual(self.come_odds_bet.status, "won", "Come Odds bet should win on 6")

    def test_come_odds_bet_cannot_be_placed_before_come_bet_moves(self):
        """Test that Come Odds bets cannot be placed before the Come bet moves to a number."""
        self.assertFalse(self.rules_engine.can_make_bet("Come Odds", "come-out"), "Come Odds bets should not be allowed during the come-out phase")

    def test_come_odds_bet_can_be_placed_after_come_bet_moves(self):
        """Test that Come Odds bets can be placed after the Come bet moves to a number."""
        # Simulate a come-out roll of 6 to move the Come bet to number 6
        dice_outcome = [3, 3]  # Total of 6
        self.rules_engine.resolve_bet(self.come_bet, dice_outcome, "point", None)
        self.assertEqual(self.come_bet.number, 6, "Come bet should move to number 6")

        # Now, Come Odds bets should be allowed
        self.assertTrue(self.rules_engine.can_make_bet("Come Odds", "point"), "Come Odds bets should be allowed during the point phase after the Come bet moves to a number")

if __name__ == "__main__":
    unittest.main()