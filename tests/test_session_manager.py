import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from craps.session_manager import SessionManager
from config import DICE_MODE

def is_interactive() -> bool:
    """Detect whether this script is running in an interactive context (not under pytest)."""
    return sys.stdin.isatty() and sys.stdout.isatty()

def test_basic_session_setup():
    print("\n🔧 Testing SessionManager setup...")
    session_mgr = SessionManager()
    max_shooters = 3
    success = session_mgr.setup_session(num_shooters=max_shooters, dice_mode=DICE_MODE)

    if not success:
        print("❌ Session initialization failed.")
        return

    print(f"🐣 Session initialized successfully!")
    print(f"🏠 House Rules: Table Min = ${session_mgr.house_rules.table_minimum}, Max = ${session_mgr.house_rules.table_maximum}")
    print(f"🧩 Game initialized with table: {bool(session_mgr.table)}, stats: {bool(session_mgr.stats)}")

    num_players = session_mgr.add_players_from_config()
    print(f"🧑‍🤝‍🧑 Players added from config: {num_players}")
    for player in session_mgr.player_lineup.get_active_players_list():
        print(f"  🧑 {player.name} [Strategy: {player.name}] — Bankroll: ${player.balance}")

    session_mgr.lock_session()
    print("🔒 Session has been locked. Players and rules are now frozen.")
    
    # 🧑‍🎤 Assign first shooter manually, others are handled by session manager
    session_mgr.assign_next_shooter()

    #   ➰ Shooter loop
    for shooter_num in range(1, max_shooters + 1):

        # Inner loop for this shooter
        while True:
            # 🪙 Collecting new player bets for this roll
            session_mgr.accept_bets()

            # 🧑‍💻 Pause for human input (only in interactive mode)
            if is_interactive():
                user_input = input("\n⏸️ Press Enter to roll the dice (or type 'quit'): ")
                if user_input.strip().lower() == 'quit':
                    print("👋 Exiting test.")
                    return

            # 🧠 Capture phase BEFORE the roll is resolved
            previous_phase = session_mgr.game_state.phase
            
            # 🎲 Roll the dice
            outcome = session_mgr.roll_dice()
            print(f"🎯 Dice outcome: {outcome[0]} + {outcome[1]} = {sum(outcome)}")

             # 💥 Resolve outcomes and update state
            session_mgr.resolve_bets(outcome)
            session_mgr.adjust_bets()
            session_mgr.refresh_bet_statuses()

            # ⚪ Puck display
            puck_msg = (
                "⚫ Puck OFF"
                if session_mgr.game_state.point is None
                else f"⚪ Puck is ON {session_mgr.game_state.point}"
            )
            print(puck_msg)

            # ❌ Handle 7-out transition
            if session_mgr.game_state.phase == "come-out" and sum(outcome) == 7:
                break  # end current shooter
            
    # 🔚 EXIT here in non-interactive mode
    if not is_interactive():
        session_mgr.finalize_session(
            stats=session_mgr.stats,
            roll_history=session_mgr.roll_history,
            roll_history_manager=session_mgr.roll_history_manager,
            play_by_play=session_mgr.play_by_play,
            players=session_mgr.player_lineup.get_active_players_list()
        )
        return

if __name__ == "__main__":
    test_basic_session_setup()
