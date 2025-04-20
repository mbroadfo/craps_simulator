from fastapi.testclient import TestClient
from craps.api.app import app
from craps.api.api_session_manager import session_manager, CrapsSession
from craps.house_rules import HouseRules

client = TestClient(app)

def test_multiple_sessions_have_isolated_house_rules_and_players():
    # Session 1: create with default rules
    rules1 = HouseRules({})
    session1 = CrapsSession(rules1)
    session_id1 = "session-1"
    session_manager.sessions[session_id1] = session1

    # Session 2: create with custom rules
    rules2 = HouseRules({"table_minimum": 25, "vig_on_win": False})
    session2 = CrapsSession(rules2)
    session_id2 = "session-2"
    session_manager.sessions[session_id2] = session2

    # GET house rules session 1
    r1 = client.get("/api/house_rules", headers={"X-Session-ID": session_id1})
    assert r1.status_code == 200
    assert r1.json()["table_minimum"] == 10
    assert r1.json()["vig_on_win"] is True

    # GET house rules session 2
    r2 = client.get("/api/house_rules", headers={"X-Session-ID": session_id2})
    assert r2.status_code == 200
    assert r2.json()["table_minimum"] == 25
    assert r2.json()["vig_on_win"] is False

    # Patch players for session 1: only Molly
    patch1 = [{"name": "Molly", "active": True}, {"name": "Fielder", "active": False}]
    p1 = client.patch("/api/players", headers={"X-Session-ID": session_id1}, json=patch1)
    assert p1.status_code == 200

    # Patch players for session 2: only Fielder
    patch2 = [{"name": "Molly", "active": False}, {"name": "Fielder", "active": True}]
    p2 = client.patch("/api/players", headers={"X-Session-ID": session_id2}, json=patch2)
    assert p2.status_code == 200

    # GET players for session 1
    list1 = client.get("/api/players", headers={"X-Session-ID": session_id1}).json()
    active1 = [p["name"] for p in list1 if p["active"]]
    print("\nSession 1 active players:", active1)
    assert active1 == ["Molly"]

    # GET players for session 2
    list2 = client.get("/api/players", headers={"X-Session-ID": session_id2}).json()
    active2 = [p["name"] for p in list2 if p["active"]]
    print("Session 2 active players:", active2)
    assert active2 == ["Fielder"]
