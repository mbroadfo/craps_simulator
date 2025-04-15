import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from craps.craps_engine import CrapsEngine
from craps.roll_history_manager import RollHistoryManager
from config import NUM_SHOOTERS

def run_session():
    # Get the session Mode
    session_mode: str = "interactive" if "--interactive" in sys.argv else "automatic"

    # Get the Dice Mode
    is_interactive = session_mode == "interactive"
    dice_mode: str = "history" if "--history" in sys.argv else "live"

    # Setup Session
    max_shooters = NUM_SHOOTERS
    session_mgr = CrapsEngine()
    roll_history_mgr = RollHistoryManager()
    success = session_mgr.setup_session(num_shooters=max_shooters, dice_mode=dice_mode, roll_history_file=roll_history_mgr.get_roll_history_file(dice_mode))
    if not success:
        return

    # Add players to session
    num_players = session_mgr.add_players_from_config()
    session_mgr.lock_session()
    
    # Assign first shooter manually, others are handled by session manager
    session_mgr.assign_next_shooter()

    #   ➰ Shooter loop
    for shooter_num in range(1, max_shooters + 1):
        # Inner loop for this shooter
        while True:
            # Collecting new player bets for this roll
            session_mgr.accept_bets()

            # 🧑‍💻 Pause for human input (only in interactive mode)
            if is_interactive:
                user_input = input("\n⏸️ Press Enter to roll the dice (or type 'auto' or 'quit'): ")
                if user_input.strip().lower() == 'quit':
                    print("👋 Exiting test.")
                    return
                elif user_input.strip().lower() == 'auto':
                    is_interactive = False

            # Capture phase BEFORE the roll is resolved
            previous_phase = session_mgr.game_state.phase
            
            # Roll the dice
            outcome = session_mgr.roll_dice()

             # Resolve outcomes and update state
            session_mgr.resolve_bets(outcome)
            session_mgr.refresh_bet_statuses()
            session_mgr.log_player_bets()

            # Handle 7-out transition
            summary = session_mgr.handle_post_roll(outcome, previous_phase)
            if summary.new_shooter_assigned:
                break  # move to next shooter
            
    # Wrap up after all shooters are done
    session_mgr.finalize_session(
        stats=session_mgr.stats,
        dice_mode=dice_mode,
        roll_history=session_mgr.roll_history,
        roll_history_manager=session_mgr.roll_history_manager,
        play_by_play=session_mgr.play_by_play,
        players=session_mgr.player_lineup.get_active_players_list()
    )
    return

if __name__ == "__main__":
    run_session()
