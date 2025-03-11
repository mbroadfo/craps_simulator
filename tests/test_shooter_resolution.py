import unittest
from craps.table import Table
from craps.player import Player
from craps.house_rules import HouseRules
from craps.rules_engine import RulesEngine
from craps.game_state import GameState

class TestShooterRotation(unittest.TestCase):

    def setUp(self):
        """Set up a table with multiple players for shooter rotation testing."""
        self.house_rules = HouseRules({})
        self.rules_engine = RulesEngine()
        self.table = Table(self.house_rules, play_by_play=False, rules_engine=self.rules_engine)
        
        # Add players to the table
        self.players = [Player(name=f"Player {i+1}") for i in range(3)]
        for player in self.players:
            self.table.add_player(player)

        # Initialize game state
        self.game_state = self.table.game_state  # Get game state from table

        # Ensure the first player is the shooter
        self.assertEqual(self.game_state.shooter_index, 0)

    def test_shooter_rotates_after_seven_out(self):
        """Shooter should rotate after rolling a seven-out."""
        first_shooter = self.game_state.shooter_index
        
        # Simulate a seven-out
        dice_roll = [4, 3]  # Total of 7
        self.table.check_bets(dice_roll, self.game_state.phase, self.game_state.point)  # Resolve roll

        # Shooter should have rotated
        self.assertNotEqual(self.game_state.shooter_index, first_shooter)
        self.assertEqual(self.game_state.shooter_index, 1)  # Next player should be the shooter

    def test_shooter_rotation_circular(self):
        """Shooter rotation should loop back to the first player after all have rolled."""
        for _ in range(len(self.players)):
            dice_roll = [4, 3]  # Seven-out
            self.table.check_bets(dice_roll, self.game_state.phase, self.game_state.point)  # Resolve roll

        # Shooter should have rotated back to the first player
        self.assertEqual(self.game_state.shooter_index, 0)

if __name__ == '__main__':
    unittest.main()
