import pytest
from fastapi.testclient import TestClient
from craps.api.app import app
from craps.api.api_session_manager import session_manager, CrapsSession
from craps.house_rules import HouseRules

client = TestClient(app)
SESSION_ID = "test-session-players"
HEADERS = {"X-Session-Key": SESSION_ID}

@pytest.fixture(autouse=True)
def inject_test_session():
    rules = HouseRules({})
    session = CrapsSession(rules)
    session_manager.sessions[SESSION_ID] = session

def test_get_players_initial():
    response = client.get("/api/players", headers=HEADERS)
    assert response.status_code == 200
    players = response.json()
    print("\n🎯 Initial GET /api/players response:")
    for player in players:
        print(f"  {player['name']} ({player['strategy']}): active={player['active']}")
    assert isinstance(players, list)
    assert all("name" in p and "strategy" in p and "active" in p for p in players)

    active_players = [p for p in players if p["active"]]
    assert len(active_players) > 0

def test_patch_only_first_player_active():
    # Fetch current player list
    response = client.get("/api/players", headers=HEADERS)
    assert response.status_code == 200
    players = response.json()

    # Create update payload: only first player remains active
    first_player = players[0]["name"]
    patch_payload = [{"name": p["name"], "active": p["name"] == first_player} for p in players]

    # Send patch
    patch_response = client.patch("/api/players", headers=HEADERS, json=patch_payload)
    assert patch_response.status_code == 200

    # Verify state
    final_response = client.get("/api/players", headers=HEADERS)
    final_players = final_response.json()
    active_players = [p for p in final_players if p["active"]]
    assert len(active_players) == 1
    assert active_players[0]["name"] == first_player
