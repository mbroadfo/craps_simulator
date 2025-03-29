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
from craps.statistics import Statistics
from tests.test_utils import assert_contains_bet

class TestStrategies(unittest.TestCase):
    """Tests for betting strategies like Pass Line and Three-Point Molly."""

    def setUp(self):
        """Set up common test environment for all strategies."""
        self.rules_engine = RulesEngine()
        self.play_by_play = PlayByPlay()
        self.house_rules = HouseRules({"table_minimum": 10, "table_maximum": 5000})
        self.player = Player(name="TestPlayer", initial_balance=1000)  # ✅ Create player first
        self.player_lineup = PlayerLineup(self.house_rules, None, self.play_by_play, self.rules_engine)
        self.player_lineup.add_player(self.player)  # ✅ Now safe
        self.table = Table(self.house_rules, self.play_by_play, self.rules_engine, self.player_lineup)
        self.stats = Statistics(self.house_rules.table_minimum, num_shooters=1, num_players=1)
        self.game_state = GameState(stats=self.stats, play_by_play=self.play_by_play)
        self.game_state.set_table(self.table)


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
                self.game_state.point = None  # Come-out phase

                bets = strategy.place_bets(self.game_state, self.player, self.table)
                if not bets:
                    continue  # No bet returned, skip this odds_type

                # ✅ Place Pass Line bet BEFORE point is established
                base_bet = bets[0]
                self.table.place_bet(base_bet, self.game_state.phase)
                self.player.balance -= base_bet.amount

                # ✅ Now establish the point
                self.game_state.point = 6
                base_bet.number = self.game_state.point

                # Confirm Pass Line bet is on the table
                matching_bet = next((b for b in self.table.bets if b.bet_type == "Pass Line" and b.owner == self.player), None)
                assert matching_bet is not None, f"Missing base bet for odds_type={odds_type}"

                # Now try placing odds
                odds_bets = strategy.adjust_bets(self.game_state, self.player, self.table)

                self.assertIsNotNone(odds_bets, f"Expected odds bet for odds_type={odds_type}")
                self.assertEqual(len(odds_bets), 1)
                self.assertEqual(odds_bets[0].bet_type, "Pass Line Odds")

                multiplier = self.rules_engine.get_odds_multiplier(odds_type, self.game_state.point)
                expected_odds_amount = 10 * multiplier
                self.assertEqual(odds_bets[0].amount, expected_odds_amount)

    def test_three_point_molly(self):
        """Test Three-Point Molly strategy placing exactly 3 bets and then stopping."""
        strategy = ThreePointMollyStrategy(table=self.table, bet_amount=10, odds_type="3x-4x-5x")

        # 1) Come-out roll
        self.game_state.point = None

        # 2) Strategy places Pass Line bet
        bets = strategy.get_bet(self.game_state, self.player, self.table)
        
        assert_contains_bet(bets, "Pass Line", self.player)

        self.table.place_bet(bets[0], self.game_state.phase)
        self.player.balance -= bets[0].amount

        # 3) Simulate point roll (e.g., point is now 6)
        self.game_state.point = 6

        # 4) Strategy should place first Come bet
        bets = strategy.get_bet(self.game_state, self.player, self.table)
        assert_contains_bet(bets, "Come", self.player)

        come_bet_1 = next(b for b in bets if b.bet_type == "Come" and b.owner == self.player)
        self.table.place_bet(come_bet_1, self.game_state.phase)
        self.player.balance -= come_bet_1.amount

        # 5) Simulate number roll → Come bet resolves to 4
        come_bet_1.number = 4

        # 6) Strategy should place second Come bet
        bets = strategy.get_bet(self.game_state, self.player, self.table)
        assert_contains_bet(bets, "Come", self.player)

        come_bet_2 = next(b for b in bets if b.bet_type == "Come" and b.owner == self.player)
        self.table.place_bet(come_bet_2, self.game_state.phase)
        self.player.balance -= come_bet_2.amount

        # 7) Simulate number roll → Come bet resolves to 9
        come_bet_2.number = 9

        # 8) Strategy should return no more bets (already has 3)
        bets = strategy.get_bet(self.game_state, self.player, self.table)
        base_bets = [b for b in bets if b.bet_type in {"Pass Line", "Come"}]
        self.assertEqual(len(base_bets), 0, "Strategy should not place more than 3 base bets")


    def test_come_odds_working_toggle(self):
        """Test that the strategy correctly toggles come odds working state."""
        strategy = ThreePointMollyStrategy(table=self.table, bet_amount=10, odds_type="3x-4x-5x")

        self.assertFalse(strategy.should_come_odds_be_working())

        # ✅ Set the toggle directly
        strategy.come_odds_working_on_come_out = True

        self.assertTrue(strategy.should_come_odds_be_working())

if __name__ == "__main__":
    unittest.main()
