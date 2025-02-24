import unittest
from craps.rules_engine import RulesEngine
from craps.bets.free_odds_bet import FreeOddsBet
from craps.bets.place_bet import PlaceBet

class TestPlaceOddsBetRules(unittest.TestCase):
    def setUp(self):
        """Initialize a Place Odds bet and the RulesEngine for testing."""
        self.player_name = "Alice"
        self.bet_amount = 100
        self.rules_engine = RulesEngine()

        # Create a Place bet and a Place Odds bet linked to it
        self.place_bet = PlaceBet(self.bet_amount, self.player_name, number=6)
        self.place_odds_bet = FreeOddsBet("Place Odds", self.bet_amount, self.player_name, parent_bet=self.place_bet)

    def test_place_odds_resolution(self):
        """Test Place Odds bet resolution during the point phase."""
        # Test winning roll (6)
        dice_outcome = [3, 3]  # Total of 6
        self.rules_engine.resolve_bet(self.place_odds_bet, dice_outcome, "point", None)
        self.assertEqual(self.place_odds_bet.status, "won", "Place Odds bet should win on 6")

        # Reset the bet for the next test
        self.place_odds_bet = FreeOddsBet("Place Odds", self.bet_amount, self.player_name, parent_bet=self.place_bet)

        # Test losing roll (7)
        dice_outcome = [3, 4]  # Total of 7
        self.rules_engine.resolve_bet(self.place_odds_bet, dice_outcome, "point", None)
        self.assertEqual(self.place_odds_bet.status, "lost", "Place Odds bet should lose on 7")

        # Reset the bet for the next test
        self.place_odds_bet = FreeOddsBet("Place Odds", self.bet_amount, self.player_name, parent_bet=self.place_bet)

        # Test non-resolving roll (8)
        dice_outcome = [4, 4]  # Total of 8
        self.rules_engine.resolve_bet(self.place_odds_bet, dice_outcome, "point", None)
        self.assertEqual(self.place_odds_bet.status, "active", "Place Odds bet should remain active on 8")

    def test_payout_ratio(self):
        """Test payout ratio for Place Odds bets."""
        # Test payout ratio for Place Odds on 6
        payout_ratio = self.rules_engine.get_payout_ratio("Place Odds", number=6)
        self.assertEqual(payout_ratio, (6, 5), "Place Odds bet on 6 should have a payout ratio of 6:5")

        # Test payout ratio for Place Odds on 4
        payout_ratio = self.rules_engine.get_payout_ratio("Place Odds", number=4)
        self.assertEqual(payout_ratio, (2, 1), "Place Odds bet on 4 should have a payout ratio of 2:1")

    def test_place_odds_linked_to_place_bet(self):
        """Test that Place Odds bets are linked to Place bets."""
        linked_bet_type = self.rules_engine.get_linked_bet_type("Place")
        self.assertEqual(linked_bet_type, "Place Odds", "Place bets should be linked to Place Odds")

    def test_place_odds_cannot_be_placed_during_come_out(self):
        """Test that Place Odds bets cannot be placed during the come-out phase."""
        self.assertFalse(
            self.rules_engine.can_make_bet("Place Odds", "come-out", parent_bet=self.place_bet),
            "Place Odds bets should not be allowed during the come-out phase"
        )

    def test_place_odds_can_be_placed_during_point_phase(self):
        """Test that Place Odds bets can be placed during the point phase."""
        self.assertTrue(
            self.rules_engine.can_make_bet("Place Odds", "point", parent_bet=self.place_bet),
            "Place Odds bets should be allowed during the point phase"
        )

if __name__ == "__main__":
    unittest.main()