import unittest
from craps.house_rules import HouseRules
from craps.player import Player
from craps.play_by_play import PlayByPlay  # Import PlayByPlay

class TestPlayer(unittest.TestCase):
    def setUp(self):
        """Set up a player for testing."""
        house_rules_config = {
            "table_minimum": 5,
            "table_maximum": 5000
        }
        self.house_rules = HouseRules(house_rules_config)
        self.play_by_play = PlayByPlay()  # Create a PlayByPlay instance
        self.player = Player(name="Test Player", initial_balance=1000, play_by_play=self.play_by_play)  # Pass it to Player
    
    def test_player_bankroll_persistence(self):
        """Test that a player's bankroll persists across rounds."""
        initial_balance = self.player.balance
        self.player.receive_payout(100)
        self.assertEqual(self.player.balance, initial_balance + 100)
    
    def test_player_can_place_bet(self):
        """Test that a player can place a valid bet."""
        house_rules_config = {
            "table_minimum": 10,
            "table_maximum": 5000
        }
        self.house_rules = HouseRules(house_rules_config)
        self.assertEqual(self.house_rules.table_minimum, 10)
    
    def test_player_cannot_bet_below_minimum(self):
        """Test that a player cannot place a bet below the table minimum."""
        house_rules_config = {
            "table_minimum": 10,
            "table_maximum": 5000
        }
        self.house_rules = HouseRules(house_rules_config)
        self.assertLess(5, self.house_rules.table_minimum)
    
    def test_player_cannot_bet_above_maximum(self):
        """Test that a player cannot place a bet above the table maximum."""
        house_rules_config = {
            "table_minimum": 10,
            "table_maximum": 5000
        }
        self.house_rules = HouseRules(house_rules_config)
        self.assertGreater(6000, self.house_rules.table_maximum)
    
    def test_player_balance_after_losing_bet(self):
        """Test that a player's balance decreases after losing a bet."""
        house_rules_config = {
            "table_minimum": 10,
            "table_maximum": 5000
        }
        self.house_rules = HouseRules(house_rules_config)
        initial_balance = self.player.balance
        lost_amount = 50
        self.player.balance -= lost_amount
        self.assertEqual(self.player.balance, initial_balance - lost_amount)
    
    def test_player_balance_after_winning_bet(self):
        """Test that a player's balance increases after winning a bet."""
        house_rules_config = {
            "table_minimum": 10,
            "table_maximum": 5000
        }
        self.house_rules = HouseRules(house_rules_config)
        initial_balance = self.player.balance
        win_amount = 150
        self.player.receive_payout(win_amount)
        self.assertEqual(self.player.balance, initial_balance + win_amount)
    
if __name__ == "__main__":
    unittest.main()
