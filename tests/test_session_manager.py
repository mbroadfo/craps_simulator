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
    success = session_mgr.setup_session(num_shooters=3)

    if success:
        print(f"✅ Session initialized successfully!")
        print(f"✅ House Rules: Table Min = ${session_mgr.house_rules.table_minimum}, Max = ${session_mgr.house_rules.table_maximum}")
        print(f"✅ Game initialized with table: {bool(session_mgr.table)}, stats: {bool(session_mgr.stats)}")

        num_players = session_mgr.add_players_from_config()
        print(f"✅ Players added from config: {num_players}")
        for player in session_mgr.player_lineup.get_active_players_list():
            print(f"  🧑 {player.name} [Strategy: {player.name}] — Bankroll: ${player.balance}")

        # Lock the session
        session_mgr.lock_session()
        print("🔒 Session has been locked. Players and rules are now frozen.")

        # Session begins
        while True:
            bet_count = session_mgr.accept_bets()
            print(f"🎲 {bet_count} bets placed for this roll.")

            if is_interactive():
                user_input = input("\n⏸️ Press Enter to roll the dice (or type 'quit' to exit): ")
                if user_input.strip().lower() == 'quit':
                    print("👋 Exiting test.")
                    break

            # Dice roll
            outcome = session_mgr.roll_dice()
            print(f"🎯 Dice outcome: {outcome[0]} + {outcome[1]} = {sum(outcome)}")

            # Resolve bets
            session_mgr.resolve_bets(outcome)
            
            # Adjust bets
            session_mgr.adjust_bets()

            # Print active bets after resolution
            for player in session_mgr.player_lineup.get_active_players_list():
                bets = [b for b in session_mgr.table.bets if b.owner == player]
                if bets:
                    for b in bets:
                        label = f"{b.bet_type} {b.number}" if b.number else b.bet_type
                        print(f" 🔘 ${player.name}'s ${b.amount} bet on {label} [{b.status}] bankroll: ${player.balance}")
            
            # Exit if not in interactive mode (prevents infinite loop in pytest)
            if not is_interactive():
                break
    else:
        print("❌ Session initialization failed.")

if __name__ == "__main__":
    test_basic_session_setup()
