import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from craps.session_manager import SessionManager

def is_interactive() -> bool:
    """Detect whether this script is running in an interactive context (not under pytest)."""
    return sys.stdin.isatty() and sys.stdout.isatty()

def test_basic_session_setup():
    print("\n🔧 Testing SessionManager setup...")
    session_mgr = SessionManager()
    max_shooters = 3
    success = session_mgr.setup_session(num_shooters=max_shooters)

    if not success:
        print("❌ Session initialization failed.")
        return

    print(f"✅ Session initialized successfully!")
    print(f"✅ House Rules: Table Min = ${session_mgr.house_rules.table_minimum}, Max = ${session_mgr.house_rules.table_maximum}")
    print(f"✅ Game initialized with table: {bool(session_mgr.table)}, stats: {bool(session_mgr.stats)}")

    num_players = session_mgr.add_players_from_config()
    print(f"✅ Players added from config: {num_players}")
    for player in session_mgr.player_lineup.get_active_players_list():
        print(f"  🧑 {player.name} [Strategy: {player.name}] — Bankroll: ${player.balance}")

    session_mgr.lock_session()
    print("🔒 Session has been locked. Players and rules are now frozen.")

    # Shooter loop
    for shooter_num in range(1, max_shooters + 1):
        shooter = session_mgr.player_lineup.get_active_players_list()[session_mgr.shooter_index % num_players]
        if session_mgr.game_state:
            session_mgr.game_state.assign_new_shooter(shooter, shooter_num)

        # Inner loop for this shooter
        while True:
            session_mgr.accept_bets()

            if is_interactive():
                user_input = input("\n⏸️ Press Enter to roll the dice (or type 'quit' to exit): ")
                if user_input.strip().lower() == 'quit':
                    print("👋 Exiting test.")
                    return

            outcome = session_mgr.roll_dice()
            print(f"🎯 Dice outcome: {outcome[0]} + {outcome[1]} = {sum(outcome)}")

            session_mgr.resolve_bets(outcome)
            
            puck_msg = "⚫ Puck OFF" if session_mgr.game_state.point == None else f"⚪ Puck is ON {session_mgr.game_state.point}"
            print(puck_msg)

            session_mgr.adjust_bets()

            # 🧾 Print player bet summary
            for player in session_mgr.player_lineup.get_active_players_list():
                remaining_bets = [b for b in session_mgr.table.bets if b.owner == player]
                if remaining_bets:
                    summary = ", ".join(
                        f"{b.bet_type} {b.number} (${b.amount} {b.status})" if b.number else f"{b.bet_type} (${b.amount} {b.status})"
                        for b in remaining_bets
                    )
                    bet_total = sum(b.amount for b in remaining_bets)
                    print(f"  📊 {player.name}'s remaining bets: {summary} | Total on table: ${bet_total} Bankroll: {player.balance}")

            # 🛑 End shooter on 7-out (detected by phase reset)
            if session_mgr.game_state.phase == "come-out" and sum(outcome) == 7:
                session_mgr.stats.record_seven_out()
                session_mgr.shooter_index += 1
                break

            # Prevent infinite loop in non-interactive test runs
            if not is_interactive():
                return

if __name__ == "__main__":
    test_basic_session_setup()
