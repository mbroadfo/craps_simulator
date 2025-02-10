import unittest
from craps.dice import Dice

class TestDice(unittest.TestCase):
    def test_roll(self):
        dice = Dice()
        for _ in range(100):  # Test 100 rolls
            outcome = dice.roll()
            self.assertIsInstance(outcome, list)
            self.assertEqual(len(outcome), 2)
            self.assertTrue(1 <= outcome[0] <= 6)
            self.assertTrue(1 <= outcome[1] <= 6)
            total = sum(outcome)
            self.assertTrue(2 <= total <= 12)

if __name__ == "__main__":
    unittest.main()