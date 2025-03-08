import unittest
from craps.rules_engine import RulesEngine
from craps.bet import Bet
from craps.table import Table
from craps.house_rules import HouseRules
from craps.play_by_play import PlayByPlay
from craps.player import Player

class TestPayouts(unittest.TestCase):
    def setUp(self):
        """Initialize the test environment."""
        # Initialize a player
        self.player = Player(name="Alice", initial_balance=1000)

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

    def test_pass_line_bet_payout(self):
        """Test payout for a Pass Line bet."""
        # Create a Pass Line bet
        pass_line_bet = self.rules_engine.create_bet("Pass Line", 100, self.player)

        # Simulate a winning roll (7 during come-out)
        pass_line_bet.status = "won"
        payout = pass_line_bet.payout()
        self.assertEqual(payout, 200, "Pass Line bet should pay 1:1 ($100 bet + $100 profit)")

    def test_place_bet_payout(self):
        """Test payout for a Place bet."""
        # Create a Place bet on 6
        place_bet = self.rules_engine.create_bet("Place", 120, self.player, number=6)

        # Simulate a winning roll (6)
        place_bet.status = "won"
        payout = place_bet.payout()
        self.assertEqual(payout, 242, "Place bet on 6 should pay 7:6 ($120 bet + $122 profit)")

    def test_field_bet_payout(self):
        """Test payout for a Field bet."""
        # Create a Field bet
        field_bet = self.rules_engine.create_bet("Field", 100, self.player)

        # Simulate a winning roll (2)
        field_bet.status = "won"
        field_bet.payout_ratio = (2, 1)  # 2:1 payout for 2
        payout = field_bet.payout()
        self.assertEqual(payout, 300, "Field bet on 2 should pay 2:1 ($100 bet + $200 profit)")

        # Simulate a winning roll (12)
        field_bet.status = "won"
        field_bet.payout_ratio = (3, 1)  # 3:1 payout for 12
        payout = field_bet.payout()
        self.assertEqual(payout, 400, "Field bet on 12 should pay 3:1 ($100 bet + $300 profit)")

        # Simulate a winning roll (3, 4, 9, 10, 11)
        field_bet.status = "won"
        field_bet.payout_ratio = (1, 1)  # 1:1 payout for other winning numbers
        payout = field_bet.payout()
        self.assertEqual(payout, 200, "Field bet on other winning numbers should pay 1:1 ($100 bet + $100 profit)")

if __name__ == "__main__":
    unittest.main()