import unittest
from craps.rules_engine import RulesEngine
from craps.table import Table
from craps.play_by_play import PlayByPlay
from craps.house_rules import HouseRules
from craps.lineup import PlayerLineup
from craps.player import Player
from craps.game_state import GameState
from craps.strategies.pass_line_strategy import PassLineStrategy
from craps.strategies.three_point_molly_strategy import ThreePointMollyStrategy

class TestStrategies(unittest.TestCase):
    """Tests for betting strategies like Pass Line and Three-Point Molly."""

    def setUp(self):
        """Set up common test environment for all strategies."""
        self.rules_engine = RulesEngine()
        self.play_by_play = PlayByPlay()
        self.house_rules = HouseRules({"table_minimum": 10, "table_maximum": 5000})
        self.player_lineup = PlayerLineup(self.house_rules, None, self.play_by_play, self.rules_engine)  # Table is None for now
        self.table = Table(self.house_rules, self.play_by_play, self.rules_engine, self.player_lineup)
        self.game_state = GameState()
        self.game_state.set_table(self.table)
        self.player = Player(name="TestPlayer", initial_balance=1000)

    def test_pass_line_base_bet(self):
        """Test placing a Pass Line bet with no odds."""
        strategy = PassLineStrategy(bet_amount=10, table=self.table)  # No odds
        bets = strategy.place_bets(self.game_state, self.player, self.table)

        self.assertEqual(len(bets), 1)
        self.assertEqual(bets[0].bet_type, "Pass Line")
        self.assertEqual(bets[0].amount, 10)

    def test_pass_line_with_odds(self):
        """Test placing a Pass Line bet with different odds types."""
        odds_types = ["1x", "2x", "3x-4x-5x", "10x"]

        for odds_type in odds_types:
            with self.subTest(odds_type=odds_type):
                strategy = PassLineStrategy(bet_amount=10, table=self.table, odds_type=odds_type)
                self.game_state.phase = "come-out"
                bets = strategy.place_bets(self.game_state, self.player, self.table)

                self.assertEqual(len(bets), 1)
                self.assertEqual(bets[0].bet_type, "Pass Line")
                self.assertEqual(bets[0].amount, 10)

                # Simulate point established
                self.game_state.phase = "point"
                self.game_state.point = 6  # Test different point numbers

                odds_bets = strategy.adjust_bets(self.game_state, self.player, self.table)

                self.assertIsNotNone(odds_bets)
                self.assertEqual(len(odds_bets), 1)
                self.assertEqual(odds_bets[0].bet_type, "Pass Line Odds")

                multiplier = self.rules_engine.get_odds_multiplier("Pass Line", self.game_state.point)
                expected_odds_amount = 10 * multiplier
                self.assertEqual(odds_bets[0].amount, expected_odds_amount)

    def test_three_point_molly(self):
        """Test Three-Point Molly strategy placing bets correctly."""
        strategy = ThreePointMollyStrategy(table=self.table, rules_engine=self.rules_engine, player_lineup=self.player_lineup, odds_type="3x-4x-5x")

        self.game_state.phase = "come-out"
        bets = strategy.get_bet(self.game_state, self.player, self.table)

        self.assertEqual(len(bets), 1)
        self.assertEqual(bets[0].bet_type, "Pass Line")

        # Simulate point established
        self.game_state.phase = "point"
        self.game_state.point = 6

        bets = strategy.get_bet(self.game_state, self.player, self.table)
        self.assertEqual(len(bets), 2)  # One Pass Line + One Come

        # Simulate a Come bet moving to a number
        self.table.bets.append(self.rules_engine.create_bet("Come", 10, self.player, number=4))

        bets = strategy.get_bet(self.game_state, self.player, self.table)
        self.assertEqual(len(bets), 3)  # Pass Line, Come, and another Come bet

    def test_come_odds_working_toggle(self):
        """Test that the strategy correctly toggles come odds working state."""
        strategy = ThreePointMollyStrategy(table=self.table, rules_engine=self.rules_engine, player_lineup=self.player_lineup, odds_type="3x-4x-5x")

        self.assertFalse(strategy.should_come_odds_be_working(self.player))

        # Simulate enabling come odds working
        self.player_lineup.set_odds_working(self.player, True)
        self.assertTrue(strategy.should_come_odds_be_working(self.player))

if __name__ == "__main__":
    unittest.main()
