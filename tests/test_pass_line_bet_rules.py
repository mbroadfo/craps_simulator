import unittest
from craps.rules_engine import RulesEngine
from craps.bet import Bet
from craps.table import Table
from craps.house_rules import HouseRules
from craps.play_by_play import PlayByPlay
from craps.player import Player

class TestPassLineBetRules(unittest.TestCase):
    def setUp(self):
        """Initialize a Pass Line bet and the RulesEngine for testing."""
        # Initialize a player
        self.player = Player(name="Alice", initial_balance=1000)

        # Initialize house rules
        self.house_rules = HouseRules({
            "table_minimum": 10,
            "table_maximum": 5000,
        })

        # Initialize play-by-play and rules engine
        self.play_by_play = PlayByPlay()
        self.rules_engine = RulesEngine()

        # Initialize the table
        self.table = Table(self.house_rules, self.play_by_play, self.rules_engine)

        # Create a Pass Line bet
        self.pass_line_bet = self.rules_engine.create_bet("Pass Line", 100, self.player)

        # Place the bet on the table
        self.table.place_bet(self.pass_line_bet, "come-out")

    def test_come_out_phase(self):
        """Test Pass Line bet behavior during the come-out phase."""
        # Test winning rolls (7, 11)
        for dice_total in [7, 11]:
            with self.subTest(dice_total=dice_total):
                dice_outcome = [dice_total // 2, dice_total // 2] if dice_total % 2 == 0 else [dice_total // 2, dice_total // 2 + 1]
                self.table.check_bets(dice_outcome, "come-out", None)
                self.assertEqual(self.pass_line_bet.status, "won", f"Pass Line bet should win on {dice_total}")

        # Test losing rolls (2, 3, 12)
        for dice_total in [2, 3, 12]:
            with self.subTest(dice_total=dice_total):
                dice_outcome = [dice_total // 2, dice_total // 2] if dice_total % 2 == 0 else [dice_total // 2, dice_total // 2 + 1]
                self.table.check_bets(dice_outcome, "come-out", None)
                self.assertEqual(self.pass_line_bet.status, "lost", f"Pass Line bet should lose on {dice_total}")

        # Test setting the point (4, 5, 6, 8, 9, 10)
        for dice_total in [4, 5, 6, 8, 9, 10]:
            with self.subTest(dice_total=dice_total):
                dice_outcome = [dice_total // 2, dice_total // 2] if dice_total % 2 == 0 else [dice_total // 2, dice_total // 2 + 1]
                self.table.check_bets(dice_outcome, "come-out", None)
                self.assertEqual(self.pass_line_bet.status, "active", f"Pass Line bet should remain active on {dice_total}")

    def test_point_phase(self):
        """Test Pass Line bet behavior during the point phase."""
        # Set the point to 6
        point = 6
        dice_outcome = [3, 3]  # Total of 6
        self.table.check_bets(dice_outcome, "come-out", None)
        self.assertEqual(self.pass_line_bet.status, "active", f"Pass Line bet should remain active on {point}")

        # Test rolls that do not resolve the bet (2, 3, 4, 5, 8, 9, 10, 11, 12)
        for dice_total in [2, 3, 4, 5, 8, 9, 10, 11, 12]:
            with self.subTest(dice_total=dice_total):
                dice_outcome = [dice_total // 2, dice_total // 2] if dice_total % 2 == 0 else [dice_total // 2, dice_total // 2 + 1]
                self.table.check_bets(dice_outcome, "point", point)
                self.assertEqual(self.pass_line_bet.status, "active", f"Pass Line bet should remain active on {dice_total}")

        # Test winning roll (point number)
        dice_outcome = [3, 3]  # Total of 6
        self.table.check_bets(dice_outcome, "point", point)
        self.assertEqual(self.pass_line_bet.status, "won", f"Pass Line bet should win on {point}")

        # Reset the bet for the next test
        self.pass_line_bet = self.rules_engine.create_bet("Pass Line", 100, self.player)
        self.table.place_bet(self.pass_line_bet, "come-out")
        self.table.check_bets([3, 3], "come-out", None)  # Set the point to 6 again

        # Test losing roll (7)
        dice_outcome = [3, 4]  # Total of 7
        self.table.check_bets(dice_outcome, "point", point)
        self.assertEqual(self.pass_line_bet.status, "lost", "Pass Line bet should lose on 7")

if __name__ == "__main__":
    unittest.main()