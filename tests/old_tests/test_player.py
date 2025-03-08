import unittest
from craps.player import Player
from craps.table import Table
from craps.bet import Bet

class TestPlayer(unittest.TestCase):
    def test_place_bet(self):
        player = Player("Alice", 1000)
        table = Table()
        player.place_bet("Pass Line", 100, table)
        self.assertEqual(player.balance, 900)
        self.assertEqual(len(player.bets), 1)
        self.assertEqual(len(table.bets), 1)

    def test_resolve_bets(self):
        player = Player("Alice", 1000)
        table = Table()
        bet = Bet("Pass Line", 100, "Alice")
        table.place_bet(bet)
        player.bets.append(bet)

        # Simulate a win
        bet.status = "won"
        player.resolve_bets(table)
        self.assertEqual(player.balance, 1100)
        self.assertEqual(len(player.bets), 0)

if __name__ == "__main__":
    unittest.main()