import sys
import os
import unittest
from craps.dice import Dice

class TestDice(unittest.TestCase):
    def test_roll(self):
        dice = Dice()
        num_rolls = 1_000_000  # Number of rolls to simulate
        tolerance = 0.001  # Tolerance for probability comparison

        # Initialize counters for single die outcomes
        single_die_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0}

        # Initialize counters for total outcomes
        total_counts = {
            2: 0, 3: 0, 4: 0, 5: 0, 6: 0,
            7: 0, 8: 0, 9: 0, 10: 0, 11: 0, 12: 0
        }

        # Roll the dice 1 million times
        for _ in range(num_rolls):
            outcome = dice.roll()
            total = sum(outcome)

            # Count single die outcomes
            for die in outcome:
                single_die_counts[die] += 1

            # Count total outcomes
            total_counts[total] += 1

        # Calculate observed probabilities for single die outcomes
        single_die_probs = {
            die: count / (num_rolls * 2)  # Each roll involves 2 dice
            for die, count in single_die_counts.items()
        }

        # Calculate observed probabilities for total outcomes
        total_probs = {
            total: count / num_rolls
            for total, count in total_counts.items()
        }

        # Expected probabilities for single die outcomes
        expected_single_die_prob = 1 / 6

        # Expected probabilities for total outcomes
        expected_total_probs = {
            2: 1 / 36,
            3: 2 / 36,
            4: 3 / 36,
            5: 4 / 36,
            6: 5 / 36,
            7: 6 / 36,
            8: 5 / 36,
            9: 4 / 36,
            10: 3 / 36,
            11: 2 / 36,
            12: 1 / 36,
        }

        # Display results for single die outcomes
        print("\nSingle Die Outcomes:")
        print(f"{'Outcome':<10} {'Actual':<10} {'Expected':<10} {'Deviation':<10}")
        for die in range(1, 7):
            actual = single_die_probs[die]
            expected = expected_single_die_prob
            deviation = actual - expected
            print(f"{die:<10} {actual:<10.6f} {expected:<10.6f} {deviation:<10.6f}")

        # Display results for total outcomes
        print("\nTotal Outcomes:")
        print(f"{'Total':<10} {'Actual':<10} {'Expected':<10} {'Deviation':<10}")
        for total in range(2, 13):
            actual = total_probs[total]
            expected = expected_total_probs[total]
            deviation = actual - expected
            print(f"{total:<10} {actual:<10.6f} {expected:<10.6f} {deviation:<10.6f}")

        # Test single die outcomes
        for die, prob in single_die_probs.items():
            self.assertAlmostEqual(
                prob,
                expected_single_die_prob,
                delta=tolerance,
                msg=f"Single die outcome {die} probability is not within tolerance."
            )

        # Test total outcomes
        for total, prob in total_probs.items():
            self.assertAlmostEqual(
                prob,
                expected_total_probs[total],
                delta=tolerance,
                msg=f"Total outcome {total} probability is not within tolerance."
            )

if __name__ == "__main__":
    unittest.main()