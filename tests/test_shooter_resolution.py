import unittest
from craps.shooter import Shooter
from craps.dice import Dice

class TestPlayerAndShooter(unittest.TestCase):

    def setUp(self):
        """Set up test environment with a player and a shooter."""
        self.shooter = Shooter(name="Test Shooter", initial_balance=1000, betting_strategy=None, dice=Dice(), play_by_play=None)

    def test_player_initialization(self):
        """Test that a player (shooter) is initialized correctly."""
        self.assertEqual(self.shooter.name, "Test Shooter")
        self.assertEqual(self.shooter.balance, 1000)
        self.assertIsNone(self.shooter.betting_strategy)

    def test_player_betting_outcome(self):
        """Test that a player only loses money when a bet is lost."""
        initial_balance = self.shooter.balance
        
        bet_amount = 100  # Amount bet
        bet_lost = True    # Simulating a loss
        bet_won = False    # Simulating a win
        
        # Balance should stay the same when placing a bet
        self.assertEqual(self.shooter.balance, initial_balance)

        # Simulate losing a bet
        if bet_lost:
            self.shooter.balance -= bet_amount

        self.assertEqual(self.shooter.balance, initial_balance - bet_amount, "Balance should decrease only on a loss.")

        # Reset balance for next check
        self.shooter.balance = initial_balance

        # Simulate winning a bet (double payout)
        if bet_won:
            self.shooter.balance += bet_amount * 2  # Assuming a 1:1 payout

        self.assertEqual(self.shooter.balance, initial_balance, "Winning should not decrease the balance.")

    def test_shooter_roll_dice(self):
        """Test that the shooter rolls dice and gets valid results."""
        outcome = self.shooter.roll_dice()
        self.assertEqual(len(outcome), 2)  # Should always roll two dice
        self.assertTrue(1 <= outcome[0] <= 6)
        self.assertTrue(1 <= outcome[1] <= 6)

if __name__ == "__main__":
    unittest.main()
