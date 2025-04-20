from fastapi.testclient import TestClient
from craps.api.app import app
from craps.api.api_session_manager import session_manager, CrapsSession
from craps.house_rules import HouseRules
from craps.player import Player

client = TestClient(app)

def test_start_game_manual_mode():
    session_id = "game-manual-test"
    rules = HouseRules({})
    session = CrapsSession(rules)
    session_manager.sessions[session_id] = session

    # ✅ Use valid strategy-backed player
    session.players.append(Player(name="FieldTest", strategy_name="Field"))

    response = client.post("/api/game/start", headers={"X-Session-ID": session_id}, json={"mode": "manual"})
    assert response.status_code == 200
    state = response.json()

    print("\n🎯 Manual Mode Game Start:")
    print(f"  Puck: {state['puck']}")
    print(f"  Point: {state['point']}")
    print(f"  Shooter Index: {state['shooter_index']}")
    print(f"  Bankrolls: {state['bankrolls']}")
    print(f"  Bets: {state['bets']}")

    assert "puck" in state and "point" in state and "bets" in state

def test_start_game_auto_mode():
    session_id = "game-auto-test"
    rules = HouseRules({})
    session = CrapsSession(rules)
    session_manager.sessions[session_id] = session

    # ✅ Use valid strategy-backed player
    session.players.append(Player(name="PassTest", strategy_name="Pass-Line"))

    response = client.post("/api/game/start", headers={"X-Session-ID": session_id}, json={"mode": "auto"})
    assert response.status_code == 200
    state = response.json()

    print("\n🤖 Auto Mode Game Start:")
    print(f"  Puck: {state['puck']}")
    print(f"  Point: {state['point']}")
    print(f"  Shooter Index: {state['shooter_index']}")
    print(f"  Bankrolls: {state['bankrolls']}")
    print(f"  Bets: {state['bets']}")

    assert isinstance(state["bankrolls"], dict)
    assert isinstance(state["bets"], list)
