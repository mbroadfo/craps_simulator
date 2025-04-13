from craps.session_manager import SessionManager
from craps.roll_history_manager import RollHistoryManager
import sys


def run_session():
    print("\n🔧 SessionManager setup...")

    # Get the session Mode
    session_mode: str = "interactive" if "--interactive" in sys.argv else "automatic"
    print(f"  🔥 Session Mode: {session_mode}")

    # Get the Dice Mode
    is_interactive = session_mode == "interactive"
    dice_mode: str = "history" if "--history" in sys.argv else "live"
    print(f"  🎲 Dice Mode: {dice_mode}")

    max_shooters = 10

    session_mgr = SessionManager()
    roll_history_mgr = RollHistoryManager()
    success = session_mgr.setup_session(num_shooters=max_shooters, dice_mode=dice_mode, roll_history_file=roll_history_mgr.get_roll_history_file(dice_mode))

    if not success:
        print("💀 Session initialization failed.")
        return

    print(f"  🏠 House Rules set: Table Min = ${session_mgr.house_rules.table_minimum}, Max = ${session_mgr.house_rules.table_maximum}")
    print(f"  🧩 Table initialized: {bool(session_mgr.table)}, stats: {bool(session_mgr.stats)}")
    print(f"🚀 Session initialized successfully!\n")

    num_players = session_mgr.add_players_from_config()
    print(f"🧑‍🤝‍🧑 {num_players} Players added from config")
    for player in session_mgr.player_lineup.get_active_players_list():
        print(f"  🙂 {player.name} [Strategy: {player.strategy_name}] — Bankroll: ${player.balance}")

    session_mgr.lock_session()
    print("🔒 Session has been locked. Players and rules are now frozen.")
    
    # 🎲🎲 Assign first shooter manually, others are handled by session manager
    session_mgr.assign_next_shooter()

    #   ➰ Shooter loop
    for shooter_num in range(1, max_shooters + 1):

        # Inner loop for this shooter
        while True:
            # 🪙 Collecting new player bets for this roll
            session_mgr.accept_bets()

            # 🧑‍💻 Pause for human input (only in interactive mode)
            if is_interactive:
                user_input = input("\n⏸️ Press Enter to roll the dice (or type 'auto' or 'quit'): ")
                if user_input.strip().lower() == 'quit':
                    print("👋 Exiting test.")
                    return
                elif user_input.strip().lower() == 'auto':
                    is_interactive = False

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
            
    # 🔚 Wrap up after all shooters are done
    session_mgr.finalize_session(
        stats=session_mgr.stats,
        dice_mode=dice_mode,
        roll_history=session_mgr.roll_history,
        roll_history_manager=session_mgr.roll_history_manager,
        play_by_play=session_mgr.play_by_play,
        players=session_mgr.player_lineup.get_active_players_list()
    )
    print(f"🔚 Session Ended!")
    return

if __name__ == "__main__":
    run_session()
