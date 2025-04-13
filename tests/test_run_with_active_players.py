import unittest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from craps.single_session import run_single_session
from craps.statistics import Statistics

class TestSingleSession(unittest.TestCase):

    def test_run_with_active_players(self):
        """
        Smoke test for full single-session run with all active players.
        Verifies that session runs to completion and outputs consistent statistics.
        """
        stats: Statistics = run_single_session(num_shooters=5)

        # ✅ Basic integrity checks
        self.assertIsInstance(stats, Statistics)
        self.assertGreater(stats.session_rolls, 0, "No rolls were recorded")
        self.assertGreater(stats.num_players, 0, "No players were loaded")

        # ✅ Validate player stats structure
        self.assertTrue(stats.player_stats, "Player statistics missing")
        for player_name, data in stats.player_stats.items():
            self.assertIn("final_bankroll", data)
            self.assertIn("bets_won", data)
            self.assertIn("bets_lost", data)

        # ✅ Validate shooter count match
        self.assertEqual(stats.num_shooters, 5, "Shooter count mismatch")

if __name__ == '__main__':
    unittest.main()
