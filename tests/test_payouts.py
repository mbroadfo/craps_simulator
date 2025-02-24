import unittest
from craps.rules_engine import RulesEngine
from craps.bets.place_bet import PlaceBet

class TestPayouts(unittest.TestCase):
    def setUp(self):
        """Initialize Place bets and the RulesEngine for testing."""
        self.player_name = "Alice"
        self.rules_engine = RulesEngine()

        # Create Place bets on different numbers
        self.place_bet_4 = PlaceBet(10, self.player_name, number=4)  # $10 on 4
        self.place_bet_5 = PlaceBet(10, self.player_name, number=5)  # $10 on 5
        self.place_bet_6 = PlaceBet(12, self.player_name, number=6)  # $12 on 6

    def test_place_bet_payouts(self):
        """Test payouts for Place bets after resolving them."""
        # Resolve the Place bet on 4 (winning roll)
        dice_outcome = [2, 2]  # Total of 4
        self.rules_engine.resolve_bet(self.place_bet_4, dice_outcome, "point", None)
        self.assertEqual(self.place_bet_4.status, "won", "Place bet on 4 should be won")
        self.assertEqual(self.place_bet_4.payout_ratio, (9, 5), "Place bet on 4 should have a payout ratio of 9:5")
        self.assertEqual(self.place_bet_4.payout(), 28, "Place bet on 4 should pay 9:5 ($18 profit + $10 original bet = $28)")

        # Resolve the Place bet on 5 (winning roll)
        dice_outcome = [3, 2]  # Total of 5
        self.rules_engine.resolve_bet(self.place_bet_5, dice_outcome, "point", None)
        self.assertEqual(self.place_bet_5.status, "won", "Place bet on 5 should be won")
        self.assertEqual(self.place_bet_5.payout_ratio, (7, 5), "Place bet on 5 should have a payout ratio of 7:5")
        self.assertEqual(self.place_bet_5.payout(), 24, "Place bet on 5 should pay 7:5 ($14 profit + $10 original bet = $24)")

        # Resolve the Place bet on 6 (winning roll)
        dice_outcome = [3, 3]  # Total of 6
        self.rules_engine.resolve_bet(self.place_bet_6, dice_outcome, "point", None)
        self.assertEqual(self.place_bet_6.status, "won", "Place bet on 6 should be won")
        self.assertEqual(self.place_bet_6.payout_ratio, (7, 6), "Place bet on 6 should have a payout ratio of 7:6")
        self.assertEqual(self.place_bet_6.payout(), 26, "Place bet on 6 should pay 7:6 ($14 profit + $12 original bet = $26)")

if __name__ == "__main__":
    unittest.main()