import unittest
from craps.rules_engine import RulesEngine
from craps.bet import Bet
from craps.table import Table
from craps.house_rules import HouseRules
from craps.play_by_play import PlayByPlay

class TestMultiplePlaceBets(unittest.TestCase):
    def setUp(self):
        """Initialize multiple Place bets and the RulesEngine for testing."""
        self.player_name = "Alice"
        self.bet_amount = 100

        # Initialize house rules
        self.house_rules = HouseRules({
            "table_minimum": 10,
            "table_maximum": 5000,
        })

        # Initialize play-by-play and rules engine
        self.play_by_play = PlayByPlay()
        self.rules_engine = RulesEngine()

        # Initialize the table
        self.table = Table(self.house_rules, self.play_by_play, self.rules_engine)

        # Create Place bets on multiple numbers
        self.place_bet_6 = self.rules_engine.create_bet("Place", self.bet_amount, self.player_name, number=6)
        self.place_bet_8 = self.rules_engine.create_bet("Place", self.bet_amount, self.player_name, number=8)
        self.place_bet_5 = self.rules_engine.create_bet("Place", self.bet_amount, self.player_name, number=5)

        # Place the bets on the table
        self.table.place_bet(self.place_bet_6, "point")
        self.table.place_bet(self.place_bet_8, "point")
        self.table.place_bet(self.place_bet_5, "point")

    def test_multiple_place_bets_resolution(self):
        """Test resolution of multiple Place bets."""
        # Simulate a roll of 6
        dice_outcome = [3, 3]  # Total of 6
        self.table.check_bets(dice_outcome, "point", None)
        resolved_bets = self.table.clear_resolved_bets()

        # Check that the Place bet on 6 is resolved as won
        self.assertEqual(self.place_bet_6.status, "won", "Place bet on 6 should win on 6")
        self.assertIn(self.place_bet_6, resolved_bets, "Place bet on 6 should be resolved")

        # Simulate a roll of 8
        dice_outcome = [4, 4]  # Total of 8
        self.table.check_bets(dice_outcome, "point", None)
        resolved_bets = self.table.clear_resolved_bets()

        # Check that the Place bet on 8 is resolved as won
        self.assertEqual(self.place_bet_8.status, "won", "Place bet on 8 should win on 8")
        self.assertIn(self.place_bet_8, resolved_bets, "Place bet on 8 should be resolved")

        # Simulate a roll of 7
        dice_outcome = [3, 4]  # Total of 7
        self.table.check_bets(dice_outcome, "point", None)
        resolved_bets = self.table.clear_resolved_bets()

        # Check that the Place bet on 5 is resolved as lost
        self.assertEqual(self.place_bet_5.status, "lost", "Place bet on 5 should lose on 7")
        self.assertIn(self.place_bet_5, resolved_bets, "Place bet on 5 should be resolved")

if __name__ == "__main__":
    unittest.main()