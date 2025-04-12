import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from craps.session_manager import SessionManager

def test_basic_session_setup():
    print("\n🔧 Testing SessionManager setup...")
    session_mgr = SessionManager()
    success = session_mgr.setup_session(num_shooters=3)

    if success:
        print("✅ Session initialized successfully!")
        print(f"House Rules: Table Min = ${session_mgr.house_rules.table_minimum}, Max = ${session_mgr.house_rules.table_maximum}")
        print(f"Game initialized with table: {bool(session_mgr.table)}, stats: {bool(session_mgr.stats)}")
    else:
        print("❌ Session initialization failed.")


if __name__ == "__main__":
    test_basic_session_setup()
