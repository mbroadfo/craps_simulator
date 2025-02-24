import unittest
from craps.rules_engine import RulesEngine
from craps.bets.place_bet import PlaceBet
from craps.bets.free_odds_bet import FreeOddsBet

class TestMultiplePlaceBets(unittest.TestCase):
    def setUp(self):
        """Initialize multiple Place bets and the RulesEngine for testing."""
        self.player_name = "Alice"
        self.bet_amount = 100
        self.rules_engine = RulesEngine()

        # Create Place bets on multiple numbers
        self.place_bet_6 = PlaceBet(self.bet_amount, self.player_name, number=6)
        self.place_bet_8 = PlaceBet(self.bet_amount, self.player_name, number=8)
        self.place_bet_5 = PlaceBet(self.bet_amount, self.player_name, number=5)

        # Create Place Odds bets linked to the Place bets
        self.place_odds_bet_6 = FreeOddsBet("Place Odds", self.bet_amount, self.player_name, parent_bet=self.place_bet_6)
        self.place_odds_bet_8 = FreeOddsBet("Place Odds", self.bet_amount, self.player_name, parent_bet=self.place_bet_8)
        self.place_odds_bet_5 = FreeOddsBet("Place Odds", self.bet_amount, self.player_name, parent_bet=self.place_bet_5)
        
    def test_multiple_place_bets_resolution(self):
        """Test resolution of multiple Place bets and their Place Odds bets."""
        # Simulate a roll of 6
        dice_outcome = [3, 3]  # Total of 6
        self.rules_engine.resolve_bet(self.place_bet_6, dice_outcome, "point", None)
        self.rules_engine.resolve_bet(self.place_odds_bet_6, dice_outcome, "point", None)
        self.assertEqual(self.place_bet_6.status, "won", "Place bet on 6 should win on 6")
        self.assertEqual(self.place_odds_bet_6.status, "won", "Place Odds bet on 6 should win on 6")

        # Simulate a roll of 8
        dice_outcome = [4, 4]  # Total of 8
        self.rules_engine.resolve_bet(self.place_bet_8, dice_outcome, "point", None)
        self.rules_engine.resolve_bet(self.place_odds_bet_8, dice_outcome, "point", None)
        self.assertEqual(self.place_bet_8.status, "won", "Place bet on 8 should win on 8")
        self.assertEqual(self.place_odds_bet_8.status, "won", "Place Odds bet on 8 should win on 8")

        # Simulate a roll of 7
        dice_outcome = [3, 4]  # Total of 7
        self.rules_engine.resolve_bet(self.place_bet_5, dice_outcome, "point", None)
        self.rules_engine.resolve_bet(self.place_odds_bet_5, dice_outcome, "point", None)
        self.assertEqual(self.place_bet_5.status, "lost", "Place bet on 5 should lose on 7")
        self.assertEqual(self.place_odds_bet_5.status, "lost", "Place Odds bet on 5 should lose on 7")

if __name__ == "__main__":
    unittest.main()