import unittest
from craps.rules_engine import RulesEngine
from craps.bet import Bet
from craps.player import Player

class TestInvalidBets(unittest.TestCase):

    def setUp(self):
        """Create a mock player for testing."""
        self.player = Player("Test Player", 1000)  # ✅ Fixed positional args

    def test_invalid_place_bets(self):
        """Test invalid Place bets (should only allow 4, 5, 6, 8, 9, 10)."""
        invalid_numbers = [2, 3, 7, 11, 12]
        for num in invalid_numbers:
            with self.assertRaises(ValueError, msg=f"Place bet on {num} should be invalid"):
                RulesEngine.create_bet("Place", 10, self.player, number=num)

    def test_invalid_hardways(self):
        """Test invalid Hardways bets (should only allow 4, 6, 8, 10)."""
        invalid_numbers = [2, 3, 5, 7, 9, 11, 12]
        for num in invalid_numbers:
            with self.assertRaises(ValueError, msg=f"Hardways bet on {num} should be invalid"):
                RulesEngine.create_bet("Hardways", 10, self.player, number=num)

    def test_invalid_field_bets(self):
        """Test invalid Field bets (should not take a number)."""
        with self.assertRaises(ValueError, msg="Field bet should not have a number"):
            RulesEngine.create_bet("Field", 10, self.player, number=5)

    def test_invalid_pass_line_bets(self):
        """Test invalid Pass Line bets (should not take a number)."""
        with self.assertRaises(ValueError, msg="Pass Line bet should not have a number"):
            RulesEngine.create_bet("Pass Line", 10, self.player, number=7)

    def test_invalid_dont_pass_bets(self):
        """Test invalid Don't Pass bets (should not take a number)."""
        with self.assertRaises(ValueError, msg="Don't Pass bet should not have a number"):
            RulesEngine.create_bet("Don't Pass", 10, self.player, number=7)

    def test_invalid_hop_bets(self):
        """Test invalid Hop bets (e.g., Hop 7-7 is not possible)."""
        with self.assertRaises(ValueError, msg="Hop 7-7 should be invalid"):
            RulesEngine.create_bet("Hop", 10, self.player, number=(7, 7))


if __name__ == "__main__":
    unittest.main()
