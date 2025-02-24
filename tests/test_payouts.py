import unittest
from craps.rules_engine import RulesEngine
from craps.bets.place_bet import PlaceBet
from craps.bets.free_odds_bet import FreeOddsBet

class TestPayouts(unittest.TestCase):
    def setUp(self):
        """Initialize Place bets and Place Odds bets for testing payouts."""
        self.player_name = "Alice"
        self.bet_amount = 100
        self.rules_engine = RulesEngine()

        # Create Place bets on different numbers
        self.place_bet_4 = PlaceBet(self.bet_amount, self.player_name, number=4)
        self.place_bet_5 = PlaceBet(self.bet_amount, self.player_name, number=5)
        self.place_bet_6 = PlaceBet(self.bet_amount, self.player_name, number=6)

        # Create Place Odds bets linked to the Place bets
        self.place_odds_bet_4 = FreeOddsBet("Place Odds", self.bet_amount, self.player_name, number=4)
        self.place_odds_bet_5 = FreeOddsBet("Place Odds", self.bet_amount, self.player_name, number=5)
        self.place_odds_bet_6 = FreeOddsBet("Place Odds", self.bet_amount, self.player_name, number=6)

    def test_place_bet_payouts(self):
        """Test payouts for Place bets."""
        # Test payout for Place bet on 4
        self.place_bet_4.status = "won"
        payout = self.place_bet_4.payout()
        self.assertEqual(payout, 190, "Place bet on 4 should pay 9:5 (190 for a 100 bet)")

        # Test payout for Place bet on 5
        self.place_bet_5.status = "won"
        payout = self.place_bet_5.payout()
        self.assertEqual(payout, 140, "Place bet on 5 should pay 7:5 (140 for a 100 bet)")

        # Test payout for Place bet on 6
        self.place_bet_6.status = "won"
        payout = self.place_bet_6.payout()
        self.assertEqual(payout, 116, "Place bet on 6 should pay 7:6 (116 for a 100 bet)")

    def test_place_odds_bet_payouts(self):
        """Test payouts for Place Odds bets."""
        # Test payout for Place Odds bet on 4
        self.place_odds_bet_4.status = "won"
        payout = self.place_odds_bet_4.payout()
        self.assertEqual(payout, 200, "Place Odds bet on 4 should pay 2:1 (200 for a 100 bet)")

        # Test payout for Place Odds bet on 5
        self.place_odds_bet_5.status = "won"
        payout = self.place_odds_bet_5.payout()
        self.assertEqual(payout, 150, "Place Odds bet on 5 should pay 3:2 (150 for a 100 bet)")

        # Test payout for Place Odds bet on 6
        self.place_odds_bet_6.status = "won"
        payout = self.place_odds_bet_6.payout()
        self.assertEqual(payout, 120, "Place Odds bet on 6 should pay 6:5 (120 for a 100 bet)")

if __name__ == "__main__":
    unittest.main()