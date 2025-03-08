import unittest
from craps.rules_engine import RulesEngine
from craps.bet import Bet
from craps.player import Player

class TestBetCreationValidation(unittest.TestCase):
    
    def setUp(self):
        """Set up a player instance for testing."""
        self.player = Player("Test Player")  # Remove 'bankroll' if it's not a valid argument
        self.player.bankroll = 1000  # Set bankroll manually if needed

    
    def test_valid_bet_creation(self):
        """Ensure bets can be created correctly in valid phases."""
        bet = RulesEngine.create_bet("Pass Line", 10, self.player)
        self.assertEqual(bet.bet_type, "Pass Line")
        self.assertEqual(bet.amount, 10)
        self.assertEqual(bet.owner, self.player)
    
    def test_invalid_bet_creation(self):
        """Ensure invalid bets raise an exception."""
        with self.assertRaises(ValueError):
            RulesEngine.create_bet("Invalid Bet", 10, self.player)
    
    def test_contract_bet_cannot_be_removed(self):
        """Ensure contract bets cannot be removed once placed."""
        bet = RulesEngine.create_bet("Pass Line", 10, self.player)
        self.assertFalse(RulesEngine.can_remove_bet(bet.bet_type, "point"))
    
    def test_valid_phases_for_bets(self):
        """Ensure bets are only allowed in correct game phases."""
        self.assertTrue(RulesEngine.can_make_bet("Pass Line", "come-out"))
        self.assertFalse(RulesEngine.can_make_bet("Pass Line", "point"))
        self.assertTrue(RulesEngine.can_make_bet("Come", "point"))
        self.assertFalse(RulesEngine.can_make_bet("Come", "come-out"))
    
    def test_bet_linkage(self):
        """Ensure linked bets (e.g., Pass Line → Pass Line Odds) are valid."""
        linked_bet = RulesEngine.get_linked_bet_type("Pass Line")
        self.assertEqual(linked_bet, "Pass Line Odds")
    
if __name__ == "__main__":
    unittest.main()
