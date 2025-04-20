from fastapi.testclient import TestClient
from craps.api.app import app
from craps.api.api_session_manager import session_manager, CrapsSession
from craps.house_rules import HouseRules
from craps.player import Player

client = TestClient(app)

def test_place_bets_for_strategy_players():
    session_id = "place-bets-test"
    rules = HouseRules({})
    session = CrapsSession(rules)
    session_manager.sessions[session_id] = session

    # ✅ Register a strategy-backed player (strategy must exist in config)
    session.players.append(Player(name="FieldTester", strategy_name="Field"))

    # Start the game
    client.post("/api/game/start", headers={"X-Session-ID": session_id})

    # Place bets
    response = client.post("/api/game/bets/place", headers={"X-Session-ID": session_id}, json={"bets": []})
    assert response.status_code == 200
    data = response.json()

    print("\n💸 Bets placed by strategy players:")
    for bet in data["bets"]:
        print(f"  {bet['owner']} - {bet['type']} (${bet['amount']})")

    assert len(data["bets"]) > 0

def test_adjust_bets_for_strategy_players():
    session_id = "adjust-bets-test"
    rules = HouseRules({})
    session = CrapsSession(rules)
    session_manager.sessions[session_id] = session

    # ✅ Register a strategy-backed player
    session.players.append(Player(name="PressTester", strategy_name="Pass-Line w/ Odds"))

    # Start the game and place bets
    client.post("/api/game/start", headers={"X-Session-ID": session_id})
    client.post("/api/game/bets/place", headers={"X-Session-ID": session_id}, json={"bets": []})

    # Adjust bets
    response = client.post("/api/game/bets/adjust", headers={"X-Session-ID": session_id}, json={"bets": []})
    assert response.status_code == 200
    data = response.json()

    print("\n🔧 Bets after adjustment by strategy:")
    for bet in data["bets"]:
        print(f"  {bet['owner']} - {bet['type']} (${bet['amount']})")

    assert len(data["bets"]) > 0
