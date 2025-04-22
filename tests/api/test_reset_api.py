from fastapi.testclient import TestClient
from craps.api.app import app
from craps.api.api_session_manager import session_manager, CrapsSession
from craps.house_rules import HouseRules
from craps.player import Player

client = TestClient(app)

def test_reset_game():
    session_id = "reset-test"
    rules = HouseRules({})
    session = CrapsSession(rules)
    session_manager.sessions[session_id] = session

    # Add a valid player
    session.players.append(Player(name="ResetGuy", strategy_name="Pass-Line"))

    # Start game initially
    start_resp = client.post("/api/game/start", headers={"X-Session-Key": session_id})
    assert start_resp.status_code == 200
    print("🎮 Initial game started")

    # Perform a roll
    roll_resp = client.post("/api/game/roll", headers={"X-Session-Key": session_id}, json={"mode": "auto"})
    assert roll_resp.status_code == 200
    print(f"🎲 First roll: {roll_resp.json()['roll']}")

    # Reset game
    reset_resp = client.post("/api/game/reset", headers={"X-Session-Key": session_id})
    assert reset_resp.status_code == 200
    reset_state = reset_resp.json()

    print("🔄 Game state after reset:")
    print(f"  Puck: {reset_state['puck']}")
    print(f"  Point: {reset_state['point']}")
    print(f"  Shooter Index: {reset_state['shooter_index']}")
    print(f"  Bankrolls: {reset_state['bankrolls']}")
    print(f"  Bets: {reset_state['bets']}")

    assert "puck" in reset_state
    assert reset_state["shooter_index"] == 1
    assert "bankrolls" in reset_state