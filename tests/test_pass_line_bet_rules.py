# File: .\tests\test_pass_line_bet_rules.py

import unittest
from typing import List
from craps.rules_engine import RulesEngine
from craps.bets.pass_line_bet import PassLineBet

class TestPassLineBetRules(unittest.TestCase):
    def setUp(self):
        """Initialize a Pass Line bet and the RulesEngine for testing."""
        self.player_name = "Alice"
        self.bet_amount = 100
        self.pass_line_bet = PassLineBet(self.bet_amount, self.player_name)
        self.rules_engine = RulesEngine()

    def test_come_out_phase(self):
        """Test Pass Line bet behavior during the come-out phase."""
        # Test winning rolls (7, 11)
        for dice_total in [7, 11]:
            with self.subTest(dice_total=dice_total):
                dice_outcome = self._get_dice_outcome(dice_total)
                self.rules_engine.resolve_bet(self.pass_line_bet, dice_outcome, "come-out", None)
                self.assertEqual(self.pass_line_bet.status, "won", f"Pass Line bet should win on {dice_total}")

        # Test losing rolls (2, 3, 12)
        for dice_total in [2, 3, 12]:
            with self.subTest(dice_total=dice_total):
                dice_outcome = self._get_dice_outcome(dice_total)
                self.rules_engine.resolve_bet(self.pass_line_bet, dice_outcome, "come-out", None)
                self.assertEqual(self.pass_line_bet.status, "lost", f"Pass Line bet should lose on {dice_total}")

        # Test setting the point (4, 5, 6, 8, 9, 10)
        for dice_total in [4, 5, 6, 8, 9, 10]:
            with self.subTest(dice_total=dice_total):
                dice_outcome = self._get_dice_outcome(dice_total)
                new_point = self.rules_engine.resolve_bet(self.pass_line_bet, dice_outcome, "come-out", None)
                self.assertEqual(self.pass_line_bet.status, "active", f"Pass Line bet should remain active on {dice_total}")
                self.assertEqual(new_point, dice_total, f"Point should be set to {dice_total}")

    def test_point_phase(self):
        """Test Pass Line bet behavior during the point phase."""
        # Set the point to 6
        point = 6
        dice_outcome = self._get_dice_outcome(point)
        new_point = self.rules_engine.resolve_bet(self.pass_line_bet, dice_outcome, "come-out", None)
        self.assertEqual(new_point, point, f"Point should be set to {point}")

        # Test rolls that do not resolve the bet (2, 3, 4, 5, 8, 9, 10, 11, 12)
        for dice_total in [2, 3, 4, 5, 8, 9, 10, 11, 12]:
            with self.subTest(dice_total=dice_total):
                dice_outcome = self._get_dice_outcome(dice_total)
                self.rules_engine.resolve_bet(self.pass_line_bet, dice_outcome, "point", point)
                self.assertEqual(self.pass_line_bet.status, "active", f"Pass Line bet should remain active on {dice_total}")

        # Test winning roll (point number)
        dice_outcome = self._get_dice_outcome(point)
        self.rules_engine.resolve_bet(self.pass_line_bet, dice_outcome, "point", point)
        self.assertEqual(self.pass_line_bet.status, "won", f"Pass Line bet should win on {point}")

        # Reset the bet for the next test
        self.pass_line_bet = PassLineBet(self.bet_amount, self.player_name)
        new_point = self.rules_engine.resolve_bet(self.pass_line_bet, self._get_dice_outcome(point), "come-out", None)
        self.assertEqual(new_point, point, f"Point should be set to {point}")

        # Test losing roll (7)
        dice_outcome = self._get_dice_outcome(7)
        self.rules_engine.resolve_bet(self.pass_line_bet, dice_outcome, "point", point)
        self.assertEqual(self.pass_line_bet.status, "lost", "Pass Line bet should lose on 7")

    def _get_dice_outcome(self, total: int) -> List[int]:
        """Helper method to generate a dice outcome for a given total."""
        if total < 2 or total > 12:
            raise ValueError("Invalid dice total. Must be between 2 and 12.")
        for die1 in range(1, 7):
            for die2 in range(1, 7):
                if die1 + die2 == total:
                    return [die1, die2]
        return None

if __name__ == "__main__":
    unittest.main()