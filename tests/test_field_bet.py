import unittest
from craps.bet import Bet
from craps.rules_engine import RulesEngine
from craps.player import Player
from craps.house_rules import HouseRules

class TestFieldBet(unittest.TestCase):
    def setUp(self):
        """Set up test environment."""
        self.house_rules = HouseRules({
            "field_bet_payout_2": (2, 1),
            "field_bet_payout_12": (3, 1),
            "table_minimum": 10,
            "table_maximum": 5000
        })
        self.rules_engine = RulesEngine()
        self.player = Player("TestPlayer", 100)
        self.bet = Bet("Field", 10, self.player)
    
    def test_field_bet_wins(self):
        """Test Field bet winning conditions and payouts."""
        winning_rolls = {
            2: (2, 1),   # Special payout for 2
            3: (1, 1),
            4: (1, 1),
            9: (1, 1),
            10: (1, 1),
            11: (1, 1),
            12: (3, 1)   # Special payout for 12
        }
        
        for roll, expected_payout in winning_rolls.items():
            with self.subTest(roll=roll):
                self.bet.status = "active"  # Reset bet status
                payout = self.rules_engine.resolve_bet(self.bet, [roll], "come-out", None)
                expected_amount = (self.bet.amount * expected_payout[0]) // expected_payout[1]
                self.assertEqual(self.bet.status, "won")
                self.assertEqual(payout, expected_amount)
    
    def test_field_bet_loses(self):
        """Test Field bet losing conditions."""
        losing_rolls = [5, 6, 7, 8]
        for roll in losing_rolls:
            with self.subTest(roll=roll):
                self.bet.status = "active"  # Reset bet status
                payout = self.rules_engine.resolve_bet(self.bet, [roll], "come-out", None)
                self.assertEqual(self.bet.status, "lost")
                self.assertEqual(payout, 0)

if __name__ == "__main__":
    unittest.main()
