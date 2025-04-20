from fastapi.testclient import TestClient
from craps.api.app import app
from craps.api.api_session_manager import session_manager, CrapsSession
from craps.house_rules import HouseRules
from craps.player import Player

client = TestClient(app)


def test_get_game_status_after_start():
    session_id = "status-test"
    rules = HouseRules({})
    session = CrapsSession(rules)
    session_manager.sessions[session_id] = session

    session.players.append(Player(name="StatMan", strategy_name="Field"))

    # Start game
    start_response = client.post("/api/game/start", headers={"X-Session-ID": session_id}, json={"mode": "manual"})
    assert start_response.status_code == 200

    # GET /status
    status_response = client.get("/api/game/status", headers={"X-Session-ID": session_id})
    assert status_response.status_code == 200

    state = status_response.json()
    print("📊 Game Status Snapshot:")
    print(f"  Puck: {state['puck']}")
    print(f"  Point: {state['point']}")
    print(f"  Shooter Index: {state['shooter_index']}")
    print(f"  Bankrolls: {state['bankrolls']}")
    print(f"  Bets: {state['bets']}")

    assert isinstance(state["bankrolls"], dict)
    assert isinstance(state["bets"], list)
