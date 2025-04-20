import pytest
from fastapi.testclient import TestClient
from craps.api.app import app
from craps.api.api_session_manager import session_manager, CrapsSession

client = TestClient(app)

# Fake session manager with preloaded session ID
SESSION_ID = "test-session-123"
HEADERS = {"X-Session-ID": SESSION_ID}

@pytest.fixture(autouse=True)
def inject_test_session():
    from craps.api.api_session_manager import session_manager
    from craps.house_rules import HouseRules

    rules = HouseRules({})
    session_manager.sessions[SESSION_ID] = CrapsSession(rules)

# === TESTS ===

def test_get_house_rules():
    response = client.get("/api/house_rules", headers=HEADERS)
    assert response.status_code == 200
    data = response.json()
    print("\n\n🎯 GET /api/house_rules response:")
    for k, v in data.items():
        print(f"  {k}: {v}")
    assert "table_minimum" in data
    assert "vig_on_win" in data


def test_patch_house_rules_partial_update():
    patch_data = {"vig_on_win": False, "table_minimum": 25}
    response = client.patch("/api/house_rules", headers=HEADERS, json=patch_data)
    assert response.status_code == 200
    result = response.json()
    assert result["rules"]["vig_on_win"] is False
    assert result["rules"]["table_minimum"] == 25

def test_post_house_rules_overwrite():
    new_rules = {
        "table_minimum": 50,
        "table_maximum": 5000,
        "vig_on_win": True,
        "number_of_shooters": 4,
        "dice_mode": "history",
        "field_bet_payout_2": 2,
        "field_bet_payout_12": 4,
        "come_odds_working_on_come_out": True,
        "leave_winning_bets_up": False,
        "leave_bets_working": True
    }
    response = client.post("/api/house_rules", headers=HEADERS, json=new_rules)
    assert response.status_code == 200
    result = response.json()
    assert result["rules"]["table_minimum"] == 50
    assert result["rules"]["leave_bets_working"] is True
