import unittest
from craps.shooter import Shooter

class TestShooter(unittest.TestCase):
    def test_roll_dice(self):
        shooter = Shooter("Alice")
        outcome = shooter.roll_dice()
        self.assertIsInstance(outcome, list)
        self.assertEqual(len(outcome), 2)
        self.assertTrue(1 <= outcome[0] <= 6)
        self.assertTrue(1 <= outcome[1] <= 6)

if __name__ == "__main__":
    unittest.main()