import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from craps.session_manager import SessionManager

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
            print(f"  🧑 {player.name} [Strategy: {player.name}]")
    else:
        print("❌ Session initialization failed.")


if __name__ == "__main__":
    test_basic_session_setup()
