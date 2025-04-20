from fastapi.testclient import TestClient
from craps.api.api_session_controller import app
from craps.api.api_session_manager import session_manager, CrapsSession
from craps.house_rules import HouseRules

client = TestClient(app)

def test_multiple_sessions_have_isolated_house_rules():
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

    # GET session 1
    r1 = client.get("/api/house_rules", headers={"X-Session-ID": session_id1})
    assert r1.status_code == 200
    assert r1.json()["table_minimum"] == 10
    assert r1.json()["vig_on_win"] is True

    # GET session 2
    r2 = client.get("/api/house_rules", headers={"X-Session-ID": session_id2})
    assert r2.status_code == 200
    assert r2.json()["table_minimum"] == 25
    assert r2.json()["vig_on_win"] is False
