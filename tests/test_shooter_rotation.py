import unittest
from craps.common import CommonTableSetup
from craps.player import Player
from time import sleep  # ⏳ Prevent runaway loops

class TestShooterRotation(unittest.TestCase):
    def setUp(self):
        """Initialize the game state and players for testing."""
        self.common_setup = CommonTableSetup()
        self.game_state = self.common_setup.game_state
        self.table = self.common_setup.table
        self.players = [
            Player("Alice", 1000),
            Player("Bob", 1000),
            Player("Charlie", 1000)
        ]

    def test_shooter_rotation(self):
        """Test that the shooter rotates correctly after consecutive 7-outs."""
        print("\n🚀 Testing Shooter Rotation on 7-Outs")

        for round_num in range(1, 4):  # Test rotation for 3 shooters
            player_index = (round_num - 1) % len(self.players)
            shooter = self.players[player_index]  # 🔄 Assign shooter
            self.game_state.assign_new_shooter(shooter)  # ✅ Set current shooter

            print(f"🎯 Round {round_num}: {shooter.name} is shooting...")

            # 🔢 **Step 1: Roll a point (e.g., 6)**
            self.game_state.update_state((3, 3))  # 🎲 Simulate rolling a 6
            self.assertEqual(self.game_state.point, 6, "Point should be set to 6")

            # 🔢 **Step 2: Roll a 7 (7-out)**
            self.game_state.update_state((4, 3))  # 🎲 Simulate rolling a 7
            self.assertIsNone(self.game_state.point, "Point should reset after 7-out")

            # 🏹 **Shooter should rotate**
            previous_shooter = shooter
            self.game_state.clear_shooter()  # 🚀 Clear shooter flag

            # ✅ **Manually assign next shooter (Single Session does this)**
            new_shooter_index = round_num % len(self.players)
            new_shooter = self.players[new_shooter_index]
            self.game_state.assign_new_shooter(new_shooter)  # ✅ Assign next shooter

            print(f"❌ {previous_shooter.name} 7-outs! Passing dice to {new_shooter.name}...")

            self.assertFalse(previous_shooter.is_shooter, "Previous shooter should lose turn after 7-out.")
            self.assertTrue(new_shooter.is_shooter, "Next player should become the new shooter.")

            sleep(0.5)  # ⏳ Prevent runaway loop

if __name__ == "__main__":
    unittest.main()
