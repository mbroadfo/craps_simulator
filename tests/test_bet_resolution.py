import unittest
from craps.rules_engine import RulesEngine
from craps.bet import Bet
from craps.player import Player

class TestBetResolution(unittest.TestCase):

    def setUp(self):
        """Set up common test data."""
        self.player = Player("Test Player")
        self.rules_engine = RulesEngine()

    def test_pass_line_win_come_out(self):
        """Pass Line bet should win on come-out roll with 7 or 11."""
        bet = self.rules_engine.create_bet("Pass Line", 10, self.player)
        payout = self.rules_engine.resolve_bet(bet, [4, 3], "come-out", None)  # Roll: 7

        self.assertEqual(bet.status, "won")
        self.assertEqual(payout, 10)  # Even money

    def test_pass_line_lose_come_out(self):
        """Pass Line bet should lose on come-out roll with 2, 3, or 12."""
        bet = self.rules_engine.create_bet("Pass Line", 10, self.player)
        payout = self.rules_engine.resolve_bet(bet, [1, 1], "come-out", None)  # Roll: 2

        self.assertEqual(bet.status, "lost")
        self.assertEqual(payout, 0)

    def test_pass_line_win_point_phase(self):
        """Pass Line bet should win when point is hit before a 7."""
        bet = self.rules_engine.create_bet("Pass Line", 10, self.player)
        payout = self.rules_engine.resolve_bet(bet, [5, 1], "point", 6)  # Roll: 6 (point hit)

        self.assertEqual(bet.status, "won")
        self.assertEqual(payout, 10)

    def test_pass_line_lose_point_phase(self):
        """Pass Line bet should lose when 7 rolls before the point."""
        bet = self.rules_engine.create_bet("Pass Line", 10, self.player)
        payout = self.rules_engine.resolve_bet(bet, [5, 2], "point", 6)  # Roll: 7

        self.assertEqual(bet.status, "lost")
        self.assertEqual(payout, 0)

    def test_field_bet_win(self):
        """Field bet should win with 2, 3, 4, 9, 10, 11, 12."""
        bet = self.rules_engine.create_bet("Field", 10, self.player)
        payout = self.rules_engine.resolve_bet(bet, [5, 5], "point", 8)  # Roll: 10

        self.assertEqual(bet.status, "won")
        self.assertEqual(payout, 10)

    def test_field_bet_special_payout(self):
        """Field bet should pay 2:1 for 2 and 3:1 for 12."""
        bet = self.rules_engine.create_bet("Field", 10, self.player)
        payout = self.rules_engine.resolve_bet(bet, [1, 1], "point", 8)  # Roll: 2

        self.assertEqual(bet.status, "won")
        self.assertEqual(payout, 20)  # 2:1 payout for rolling a 2

    def test_field_bet_loss(self):
        """Field bet should lose with 5, 6, 7, 8."""
        bet = self.rules_engine.create_bet("Field", 10, self.player)
        payout = self.rules_engine.resolve_bet(bet, [4, 1], "point", 8)  # Roll: 5

        self.assertEqual(bet.status, "lost")
        self.assertEqual(payout, 0)

if __name__ == "__main__":
    unittest.main()
