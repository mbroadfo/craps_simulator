from fastapi.testclient import TestClient
from craps.api.app import app
from craps.api.api_session_manager import session_manager, CrapsSession
from craps.house_rules import HouseRules
from craps.player import Player

client = TestClient(app)

def setup_game_session(session_id: str, strategy_name: str) -> None:
    rules = HouseRules({})
    session = CrapsSession(rules)
    session.players.append(Player(name="TestPlayer", strategy_name=strategy_name))
    session_manager.sessions[session_id] = session

    # Start game
    client.post("/api/game/start", headers={"X-Session-ID": session_id}, json={"mode": "manual"})

def test_roll_manual_dice():
    session_id = "roll-manual-test"
    setup_game_session(session_id, strategy_name="Pass-Line")

    response = client.post("/api/game/roll", headers={"X-Session-ID": session_id}, json={
        "mode": "manual",
        "dice": [3, 4]
    })
    assert response.status_code == 200
    data = response.json()
    print("🎲 Manual Roll:", data["roll"])
    assert data["roll"] == [3, 4]
    assert "roll_number" in data
    assert "bankrolls" in data

def test_roll_auto_dice():
    session_id = "roll-auto-test"
    setup_game_session(session_id, strategy_name="Pass-Line")

    response = client.post("/api/game/roll", headers={"X-Session-ID": session_id}, json={
        "mode": "auto"
    })
    assert response.status_code == 200
    data = response.json()
    print("🎲 Auto Roll:", data["roll"])
    assert isinstance(data["roll"], list) and len(data["roll"]) == 2
    assert "roll_number" in data
    assert "bankrolls" in data
