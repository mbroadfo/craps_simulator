import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from craps.craps_engine import CrapsEngine

def test_quiet_mode_session():
    engine = CrapsEngine(quiet_mode=True)
    engine.setup_session(num_shooters=10, num_players=10)  # use config.py players
    engine.add_players_from_config()
    engine.lock_session()

    while engine.shooter_index < engine.stats.num_shooters:
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
                break

    # Finalize
    stats = engine.finalize_session(
        stats=engine.stats,
        dice_mode="live",
        roll_history=engine.roll_history,
        roll_history_manager=engine.roll_history_manager,
        play_by_play=engine.play_by_play,
        players=engine.player_lineup.get_active_players_list()
    )

    print("✅ Quiet mode session ran successfully.")
    print(f"Total rolls: {stats.session_rolls}")
    print(f"Total amount bet: {stats.total_amount_bet}")
    print(f"House take: {stats.house_take()}")
    print(f"7s rolled: {stats.total_sevens}")

if __name__ == "__main__":
    test_quiet_mode_session()
