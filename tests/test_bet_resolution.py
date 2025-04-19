import unittest
from craps.rules_engine import RulesEngine
from craps.bet import Bet
from craps.player import Player
from craps.common import CommonTableSetup
from craps.statistics import Statistics
from craps.game_state import GameState

class TestBetResolution(unittest.TestCase):

    def setUp(self):
        """Set up common test data."""
        self.player = Player("Test Player")
        self.common_setup = CommonTableSetup()
        self.rules_engine = RulesEngine()
        self.min_bet = self.common_setup.house_rules.table_minimum
        self.statistics = Statistics(table_minimum=self.min_bet, num_shooters=1, num_players=1)
        self.game_state = GameState(self.statistics)
        self.player = self.common_setup.player


    ### ✅ Line Bets ###
    def test_pass_line_win_come_out(self):
        """Pass Line bet should win on come-out roll with 7 or 11."""
        bet = self.rules_engine.create_bet("Pass Line", 10, self.player)
        self.game_state.point = None # come-out
        payout = self.rules_engine.resolve_bet(bet, [4, 3], self.game_state)  # front-line winner

        self.assertEqual(bet.status, "won")
        self.assertEqual(payout, 10)  # Even money

    def test_pass_line_lose_come_out(self):
        """Pass Line bet should lose on come-out roll with 2, 3, or 12."""
        bet = self.rules_engine.create_bet("Pass Line", 10, self.player)
        self.game_state.point = None # come-out
        payout = self.rules_engine.resolve_bet(bet, [1, 1], self.game_state)  # Craps

        self.assertEqual(bet.status, "lost")
        self.assertEqual(payout, 0)

    ### ✅ Proposition Bets (Updated) ###
    def test_proposition_win(self):
        """Proposition bet should win when the exact number is rolled."""
        bet = self.rules_engine.create_bet("Proposition", 10, self.player, number=11)  # Yo (11)
        self.game_state.point = 8 # point
        payout = self.rules_engine.resolve_bet(bet, [6, 5], self.game_state)  # Roll: 11

        self.assertEqual(bet.status, "won")
        self.assertGreater(payout, 0)

    def test_proposition_loss(self):
        """Proposition bet should lose on any number except its specific value."""
        bet = self.rules_engine.create_bet("Proposition", 10, self.player, number=11)  # Yo (11)
        self.game_state.point = 8 # point
        payout = self.rules_engine.resolve_bet(bet, [3, 4], self.game_state)  # 7-out

        self.assertEqual(bet.status, "lost")
        self.assertEqual(payout, 0)

    ### ✅ Any 7 Bet (Updated to Proposition) ###
    def test_proposition_7_win(self):
        """Any 7 bet should win when a 7 is rolled."""
        bet = self.rules_engine.create_bet("Proposition", 10, self.player, number=7)
        self.game_state.point = 8 # point
        payout = self.rules_engine.resolve_bet(bet, [5, 2], self.game_state)  # Big Red

        self.assertEqual(bet.status, "won")
        self.assertGreater(payout, 0)

    def test_proposition_7_loss(self):
        """Any 7 bet should lose on any roll except 7."""
        bet = self.rules_engine.create_bet("Proposition", 10, self.player, number=7)
        self.game_state.point = 8 # point
        payout = self.rules_engine.resolve_bet(bet, [6, 5], self.game_state)  # Prop loss

        self.assertEqual(bet.status, "lost")
        self.assertEqual(payout, 0)

    ### ✅ Field Bets (Ensure Proper Payouts) ###
    def test_field_bet_special_payout(self):
        """Field bet should pay 2:1 for 2 and 3:1 for 12."""
        bet = self.rules_engine.create_bet("Field", 10, self.player)
        self.game_state.point = 8 # point
        payout = self.rules_engine.resolve_bet(bet, [1, 1], self.game_state)  # Aces

        self.assertEqual(bet.status, "won")
        self.assertEqual(payout, 20)  # 2:1 payout for rolling a 2

    ### ✅ Hardways ###
    def test_hardways_win(self):
        """Hardways bet should win when the exact hardway is rolled."""
        bet = self.rules_engine.create_bet("Hardways", 10, self.player, number=8)
        self.game_state.point = 8 # point
        payout = self.rules_engine.resolve_bet(bet, [4, 4], self.game_state)  # Hard 8

        self.assertEqual(bet.status, "won")
        self.assertGreater(payout, 0)

    def test_hardways_loss_easy_way(self):
        """Hardways bet should lose if the same total is rolled the easy way."""
        bet = self.rules_engine.create_bet("Hardways", 10, self.player, number=8)
        self.game_state.point = 8 # point
        payout = self.rules_engine.resolve_bet(bet, [5, 3], self.game_state)  # Easy 8

        self.assertEqual(bet.status, "lost")
        self.assertEqual(payout, 0)

    def test_hardways_loss_seven(self):
        """Hardways bet should lose when a 7 is rolled."""
        bet = self.rules_engine.create_bet("Hardways", 10, self.player, number=8)
        self.game_state.point = 8 # point
        payout = self.rules_engine.resolve_bet(bet, [5, 2], self.game_state)  # 7-out

        self.assertEqual(bet.status, "lost")
        self.assertEqual(payout, 0)

if __name__ == "__main__":
    unittest.main()
