import unittest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import HOUSE_RULES, DICE_MODE
from craps.craps_engine import CrapsEngine
from craps.roll_history_manager import RollHistoryManager
class TestSingleSession(unittest.TestCase):

    def test_run_with_active_players(self):
        """Smoke test for full single-session run with all active players."""
        engine = CrapsEngine()
        roll_history_mgr = RollHistoryManager()

        roll_history_mgr.prepare_for_session(DICE_MODE)
        roll_file = roll_history_mgr.get_roll_history_file(DICE_MODE)

        success = engine.setup_session(
            house_rules_dict=HOUSE_RULES,
            num_shooters=5,
            dice_mode=DICE_MODE,
            roll_history_file=roll_file
        )

        self.assertTrue(success, "Failed to set up session")

        num_players = engine.add_players_from_config()
        self.assertGreater(num_players, 0, "No active players were added")

        engine.lock_session()
        engine.assign_next_shooter()

        while True:
            engine.accept_bets()
            prev_phase = engine.game_state.phase
            outcome = engine.roll_dice()
            engine.resolve_bets(outcome)
            engine.refresh_bet_statuses()
            engine.log_player_bets()

            post = engine.handle_post_roll(outcome, prev_phase)
            if post.new_shooter_assigned:
                if engine.shooter_index >= engine.stats.num_shooters:
                    break

        stats = engine.finalize_session(
            stats=engine.stats,
            dice_mode=DICE_MODE,
            roll_history=engine.roll_history,
            roll_history_manager=engine.roll_history_manager,
            play_by_play=engine.play_by_play,
            players=engine.player_lineup.get_active_players_list(),
        )

        self.assertGreater(stats.session_rolls, 0, "No rolls were recorded")
        self.assertEqual(stats.num_players, num_players)
        self.assertEqual(stats.num_shooters, 5)

        for name, data in stats.player_stats.items():
            self.assertIn("bets_lost", data)
            self.assertIn("bets_won", data)
            self.assertIn("net_win_loss", data)
            self.assertIn("final_bankroll", data)

if __name__ == "__main__":
    unittest.main()
