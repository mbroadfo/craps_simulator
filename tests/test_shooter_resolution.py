import unittest
from craps.common import CommonTableSetup
from craps.shooter import Shooter

class TestShooterRotation(unittest.TestCase):
    def setUp(self):
        """Initialize the table and players correctly."""
        self.common_setup = CommonTableSetup()
        self.table = self.common_setup.table
        self.players = [self.common_setup.player]  # Use existing setup
        
    def test_shooter_rotates_after_seven_out(self):
        """Shooter should rotate after rolling a seven-out."""
        shooter = Shooter(self.players[0].name)
        self.table.current_shooter = shooter

        # Simulate a 7-out
        shooter.roll_dice = lambda: [4, 3]  # Force a roll of 7
        self.table.check_bets([4, 3], "point", 6)  # Removed puck_position

        # Ensure shooter rotates (this part depends on your game logic)
        new_shooter = self.table.current_shooter
        self.assertNotEqual(shooter, new_shooter, "Shooter did not rotate after a seven-out.")

    def test_shooter_rotation_circular(self):
        """Shooter rotation should loop back to the first player after all have rolled."""
        self.players.append(Shooter("Bob"))
        self.players.append(Shooter("Charlie"))

        self.table.current_shooter = self.players[0]  # Start with first shooter

        for _ in range(len(self.players)):
            self.table.current_shooter.roll_dice = lambda: [4, 3]  # Force 7-out
            self.table.check_bets([4, 3], "point", 6)  # Removed puck_position

        # After all players shoot, it should return to the first shooter
        self.assertEqual(self.table.current_shooter, self.players[0], "Shooter rotation did not loop back.")

if __name__ == "__main__":
    unittest.main()
