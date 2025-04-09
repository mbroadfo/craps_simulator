import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
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
from craps.strategies.iron_cross_strategy import IronCrossStrategy
from craps.strategies.double_hop_strategy import DoubleHopStrategy
from craps.strategies.three_two_one_strategy import ThreeTwoOneStrategy
from craps.statistics import Statistics
from craps.strategies.place_reggression_strategy import PlaceRegressionStrategy
from craps.strategies.adjuster_only_strategy import AdjusterOnlyStrategy
from craps.bet_adjusters import HalfPressAdjuster
from craps.strategies.regress_then_press_strategy import RegressThenPressStrategy
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

        base_bet = bets[0]
        self.table.place_bet(base_bet, self.game_state.phase)
        self.player.balance -= base_bet.amount

        # Simulate point being established
        self.game_state.point = 6
        base_bet.number = 6

        # Strategy should not place more bets
        bets = strategy.place_bets(self.game_state, self.player, self.table)
        self.assertFalse(bets, "Expected no bets after point is established")

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

                # Strategy should not place more bets
                bets = strategy.place_bets(self.game_state, self.player, self.table)
                self.assertFalse(bets, "Expected no bets after point is established")

    def test_three_point_molly(self):
        """Test Three-Point Molly strategy placing exactly 3 bets and then stopping."""
        strategy = ThreePointMollyStrategy(table=self.table, bet_amount=10, odds_type="3x-4x-5x")

        # 1) Come-out roll
        self.game_state.point = None

        # 2) Strategy places Pass Line bet
        bets = strategy.place_bets(self.game_state, self.player, self.table)
        
        assert_contains_bet(bets, "Pass Line", self.player)

        self.table.place_bet(bets[0], self.game_state.phase)
        self.player.balance -= bets[0].amount

        # 3) Simulate point roll (e.g., point is now 6)
        self.game_state.point = 6

        # 4) Strategy should place first Come bet
        bets = strategy.place_bets(self.game_state, self.player, self.table)
        assert_contains_bet(bets, "Come", self.player)

        come_bet_1 = next(b for b in bets if b.bet_type == "Come" and b.owner == self.player)
        self.table.place_bet(come_bet_1, self.game_state.phase)
        self.player.balance -= come_bet_1.amount

        # 5) Simulate number roll → Come bet resolves to 4
        come_bet_1.number = 4

        # 6) Strategy should place second Come bet
        bets = strategy.place_bets(self.game_state, self.player, self.table)
        assert_contains_bet(bets, "Come", self.player)

        come_bet_2 = next(b for b in bets if b.bet_type == "Come" and b.owner == self.player)
        self.table.place_bet(come_bet_2, self.game_state.phase)
        self.player.balance -= come_bet_2.amount

        # 7) Simulate number roll → Come bet resolves to 9
        come_bet_2.number = 9

        # 8) Strategy should return no more bets (already has 3)
        bets = strategy.place_bets(self.game_state, self.player, self.table)
        base_bets = [b for b in bets if b.bet_type in {"Pass Line", "Come"}]
        self.assertEqual(len(base_bets), 0, "Strategy should not place more than 3 base bets")


    def test_come_odds_working_toggle(self):
        """Test that the strategy correctly toggles come odds working state."""
        strategy = ThreePointMollyStrategy(table=self.table, bet_amount=10, odds_type="3x-4x-5x")

        self.assertFalse(strategy.should_come_odds_be_working())

        # ✅ Set the toggle directly
        strategy.come_odds_working_on_come_out = True

        self.assertTrue(strategy.should_come_odds_be_working())

    def test_iron_cross_strategy(self):
        """Test Iron Cross strategy behavior before and after point is set."""
        strategy = IronCrossStrategy(
            table=self.table,
            rules_engine=self.rules_engine,
            min_bet=self.house_rules.table_minimum,
            play_by_play=self.play_by_play
        )

        # Come-out: should place Pass Line bet only
        self.game_state.point = None
        bets = strategy.place_bets(self.game_state, self.player, self.table)
        assert_contains_bet(bets, "Pass Line", self.player)
        base_bet = bets[0]
        self.table.place_bet(base_bet, self.game_state.phase)
        self.player.balance -= base_bet.amount

        # Simulate point set
        self.game_state.point = 6
        base_bet.number = 6

        # Place Iron Cross setup bets
        bets = strategy.place_bets(self.game_state, self.player, self.table)
        bet_types = [b.bet_type for b in bets]
        self.assertIn("Place", bet_types)
        self.assertIn("Field", bet_types)

        for b in bets:
            self.table.place_bet(b, self.game_state.phase)
            self.player.balance -= b.amount

        # Retry — should return no additional bets
        bets = strategy.place_bets(self.game_state, self.player, self.table)
        self.assertFalse(bets, "Expected no additional bets once Iron Cross is established")

    def setUp(self):
        self.rules_engine = RulesEngine()
        self.play_by_play = PlayByPlay()
        self.house_rules = HouseRules({"table_minimum": 10, "table_maximum": 5000})
        self.player = Player(name="DoubleHopTester", initial_balance=1000)
        self.player_lineup = PlayerLineup(self.house_rules, None, self.play_by_play, self.rules_engine)
        self.player_lineup.add_player(self.player)
        self.table = Table(self.house_rules, self.play_by_play, self.rules_engine, self.player_lineup)
        self.stats = Statistics(self.house_rules.table_minimum, num_shooters=1, num_players=1)
        self.game_state = GameState(stats=self.stats, play_by_play=self.play_by_play)
        self.game_state.set_table(self.table)
        self.strategy = DoubleHopStrategy(hop_target=(1, 1), rules_engine=self.rules_engine, base_bet=10)
        self.player.betting_strategy = self.strategy

    def test_initial_placement(self):
        bets = self.strategy.place_bets(self.game_state, self.player, self.table)
        self.assertEqual(len(self.table.bets), 1)
        hop_bet = self.table.bets[0]
        self.assertEqual(hop_bet.number, (1, 1))
        self.assertEqual(hop_bet.amount, 10)
        self.assertEqual(hop_bet.bet_type, "Hop")

    def test_press_and_reset_cycle(self):
        # Step 1: Place initial bet
        self.strategy.place_bets(self.game_state, self.player, self.table)
        hop_bet = self.table.bets[0]

        # Step 2: First win (should press to 310)
        hop_bet.status = "won"
        hop_bet.resolved_payout = 300
        hop_bet.hits += 1
        self.strategy.adjust_bets(self.game_state, self.player, self.table)
        self.assertEqual(hop_bet.amount, 310)

        # Step 3: Second win (should reset to base bet)
        hop_bet.status = "won"
        hop_bet.resolved_payout = 9300
        hop_bet.hits += 1
        self.strategy.adjust_bets(self.game_state, self.player, self.table)
        self.assertEqual(hop_bet.amount, 10)

    def test_three_two_one_strategy(self):
        # Set up the strategy
        strategy = ThreeTwoOneStrategy(self.rules_engine, min_bet=10)
        self.player.betting_strategy = strategy

        # Step 1: Come-out → expect Pass Line only
        self.game_state.point = None  # Come-out
        bets = strategy.place_bets(self.game_state, self.player, self.table)
        self.assertEqual(len(bets), 1)
        self.assertEqual(bets[0].bet_type, "Pass Line")

        self.table.place_bet(bets[0], self.game_state.phase)
        self.player.balance -= bets[0].amount

        # Step 2: Point is set to 5
        self.game_state.point = 5

        # Step 3: Place inside bets (should exclude 5), and odds
        bets = strategy.place_bets(self.game_state, self.player, self.table)
        bet_types = [b.bet_type for b in bets]
        numbers = [b.number for b in bets if b.bet_type == "Place"]

        self.assertIn("Pass Line Odds", bet_types)
        self.assertCountEqual(numbers, [6, 8, 9])

        for bet in bets:
            self.table.place_bet(bet, self.game_state.phase)
            self.player.balance -= bet.amount

        # Step 4: Simulate 3 hits (6, 8, 9 all win)
        for bet in self.table.bets:
            if bet.bet_type == "Place":
                bet.status = "won"

        strategy.adjust_bets(self.game_state, self.player, self.table)

        # Step 5: Verify that place bets were turned off
        for bet in self.table.bets:
            if bet.bet_type == "Place":
                self.assertEqual(bet.status, "inactive")

        # Step 6: Simulate 5 rolled (point hit)
        for bet in self.table.bets:
            if bet.bet_type in {"Pass Line", "Pass Line Odds"}:
                bet.status = "won"

        # Simulate resolution — not verifying payout here
        # Step 7: Set puck off (new come-out)
        self.game_state.point = None # Come-out
        strategy.adjust_bets(self.game_state, self.player, self.table)  # Should reset state

        # Step 8: New point → place bets should come back alive
        self.game_state.point = 10  # Point
        strategy.place_bets(self.game_state, self.player, self.table)

        for bet in self.table.bets:
            if bet.bet_type == "Place":
                self.assertEqual(bet.status, "active")

    def test_regress_then_half_press_strategy(self):
        """Test RegressThenPressStrategy cycles between regress and press within same shooter."""

        unit_levels = [20, 10, 5, 3]

        regression_strategy = PlaceRegressionStrategy(
            high_unit=unit_levels[0],
            low_unit=unit_levels[-1],
            regression_factor=2
        )

        press_strategy = AdjusterOnlyStrategy(
            name="Half Press",
            adjuster=HalfPressAdjuster()
        )

        strategy = RegressThenPressStrategy(
            regression_strategy=regression_strategy,
            press_strategy=press_strategy
        )

        self.player.betting_strategy = strategy
        self.game_state.point = 6  # Simulate point established

        # Phase 1: Start in regression mode
        bets = strategy.place_bets(self.game_state, self.player, self.table)
        self.assertEqual(len(bets), 4)
        self.assertIs(strategy.active_strategy, regression_strategy)
        self.assertFalse(strategy.transitioned)

        for bet in bets:
            self.table.place_bet(bet, self.game_state.phase)
            self.player.balance -= bet.amount

        # Simulate enough wins to transition to press mode
        for _ in range(5):  # simulate enough profit to exceed exposure
            strategy.notify_payout(140)

        self.assertTrue(strategy.transitioned)
        self.assertIs(strategy.active_strategy, press_strategy)

        # Phase 2: In press mode
        place_bet = next(b for b in self.table.bets if b.bet_type == "Place" and b.number == 6)
        place_bet.status = "won"
        place_bet.resolved_payout = 140
        self.stats.last_roll_total = 6

        updated_bets = strategy.adjust_bets(self.game_state, self.player, self.table)
        self.assertIsNotNone(updated_bets)

        # Simulate pressing that pushes us back to original unit level
        while strategy.transitioned:
            place_bet.status = "won"
            place_bet.resolved_payout = 140
            self.stats.last_roll_total = 6
            updated_bets = strategy.adjust_bets(self.game_state, self.player, self.table)

        # Phase 3: Back to regression
        self.assertFalse(strategy.transitioned)
        self.assertIs(strategy.active_strategy, regression_strategy)

        # Simulate enough wins to return to press mode again
        for _ in range(5):
            strategy.notify_payout(140)

        self.assertTrue(strategy.transitioned)
        self.assertIs(strategy.active_strategy, press_strategy)

    def test_three_point_dolly(self):
        """Test Three-Point Dolly strategy places Don't Pass, Don't Come, and Lay Odds correctly."""
        from craps.strategies.three_point_dolly_strategy import ThreePointDollyStrategy

        strategy = ThreePointDollyStrategy(table=self.table, bet_amount=10, odds_type="3x-4x-5x")
        self.player.betting_strategy = strategy

        # 1) Come-out roll — should place Don't Pass
        self.game_state.point = None
        bets = strategy.place_bets(self.game_state, self.player, self.table)
        assert_contains_bet(bets, "Don't Pass", self.player)

        dp_bet = bets[0]
        self.table.place_bet(dp_bet, self.game_state.phase)
        self.player.balance -= dp_bet.amount

        # 2) Point is established (e.g., 8)
        self.game_state.point = 8

        # 3) Should place Don't Come and lay odds on Don't Pass
        bets = strategy.place_bets(self.game_state, self.player, self.table)
        assert_contains_bet(bets, "Don't Come", self.player)
        assert_contains_bet(bets, "Don't Pass Odds", self.player)

        for b in bets:
            self.table.place_bet(b, self.game_state.phase)
            self.player.balance -= b.amount

        # 4) Simulate Don't Come bet moving to 5
        dc_bet = next(b for b in self.table.bets if b.bet_type == "Don't Come")
        dc_bet.number = 5

        # 5) Place second Don't Come and odds on the first
        bets = strategy.place_bets(self.game_state, self.player, self.table)
        assert_contains_bet(bets, "Don't Come", self.player)
        assert_contains_bet(bets, "Don't Come Odds", self.player)

        for b in bets:
            self.table.place_bet(b, self.game_state.phase)
            self.player.balance -= b.amount

        # 6) Simulate second Don't Come moving to 9
        second_dc = next(b for b in self.table.bets if b.bet_type == "Don't Come" and b.number is None)
        second_dc.number = 9

        # 7) Try placing more Don't Come bets → should NOT place (already have 2 DC points)
        bets = strategy.place_bets(self.game_state, self.player, self.table)
        base_dont_come_bets = [b for b in bets if b.bet_type == "Don't Come"]
        self.assertEqual(len(base_dont_come_bets), 0, "Should not place more than 2 Don't Come bets")

if __name__ == "__main__":
    unittest.main()
