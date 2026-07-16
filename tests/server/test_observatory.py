"""Step 1 gate tests: SSE stream, gapless reconnect, controls, replay
paging, and D6 enforcement — all through the HTTP surface.

TestClient runs the app's event loop in a portal thread, so the drive
task makes progress while the test thread polls or sleeps.
"""
import json
import time

import pytest
from fastapi.testclient import TestClient

from craps.server.app import create_app

LINEUP = [
    {"name": "Linus", "strategy": "Pass-Line"},
    {"name": "Fielder", "strategy": "Field"},
]


@pytest.fixture
def client(tmp_path):
    app = create_app(sessions_dir=tmp_path / "sessions")
    with TestClient(app) as test_client:
        yield test_client


def create_table(client, **overrides):
    body = {
        "table_id": "t1",
        "players": LINEUP,
        "num_shooters": 2,
        "dice_seed": 42,
        "roll_delay_ms": 0,
        **overrides,
    }
    resp = client.post("/tables", json=body)
    assert resp.status_code == 201, resp.text
    return resp.json()


def wait_for_state(client, table_id, state, timeout=20):
    deadline = time.time() + timeout
    snap = None
    while time.time() < deadline:
        snap = client.get(f"/tables/{table_id}").json()
        if snap["state"] == state:
            return snap
        time.sleep(0.02)
    raise AssertionError(f"{table_id} never reached {state!r}; last: {snap}")


def iter_frames(response):
    """Parse SSE lines into {id, event, data} frames."""
    frame = {}
    for line in response.iter_lines():
        if line == "":
            if frame:
                yield frame
                frame = {}
        elif line.startswith("id: "):
            frame["id"] = int(line[len("id: "):])
        elif line.startswith("event: "):
            frame["event"] = line[len("event: "):]
        elif line.startswith("data: "):
            frame["data"] = json.loads(line[len("data: "):])


# ---------------------------------------------------------------- lifecycle

def test_create_start_finish_and_stats(client):
    snap = create_table(client)
    assert snap["state"] == "created"
    assert snap["players"][0] == {
        "name": "Linus", "strategy": "Pass-Line", "bankroll": None,
    }

    assert client.post("/tables/t1/start").status_code == 200
    snap = wait_for_state(client, "t1", "finished")
    assert snap["session_rolls"] > 0
    assert snap["players"][0]["name"] == "Linus"
    assert isinstance(snap["players"][0]["bankroll"], int)

    stats = client.get("/tables/t1/stats").json()
    assert stats["session_rolls"] == snap["session_rolls"]
    assert set(stats["bankroll_history"]) == {"Linus", "Fielder"}
    assert stats["total_amount_bet"] > 0

    # D5: per-player realized vs theoretical edge rides the stats payload
    edges = stats["edges"]
    assert edges["Fielder"]["theoretical_edge_pct"] == pytest.approx(-100 / 36)
    for edge_snapshot in edges.values():
        assert edge_snapshot["wagered"] > 0
        assert edge_snapshot["edge_delta_pct"] == pytest.approx(
            edge_snapshot["realized_edge_pct"] - edge_snapshot["theoretical_edge_pct"]
        )

    recordings = client.get("/recordings").json()
    assert len(recordings) == 1
    assert recordings[0]["name"].startswith("t1_")


def test_strategy_list_matches_lineup_vocabulary(client):
    strategies = client.get("/tables/strategies").json()
    assert "Pass-Line" in strategies
    assert "Iron Cross" in strategies
    assert strategies == sorted(strategies)
    # the route must not be shadowed by /tables/{table_id}
    assert isinstance(strategies, list)


def test_validation_errors(client):
    create_table(client)
    # duplicate table_id
    resp = client.post("/tables", json={"table_id": "t1", "players": LINEUP})
    assert resp.status_code == 409
    # unknown strategy
    resp = client.post("/tables", json={
        "table_id": "t2",
        "players": [{"name": "X", "strategy": "Martingale"}],
    })
    assert resp.status_code == 422
    assert "Martingale" in resp.text
    # unknown table
    assert client.get("/tables/nope").status_code == 404
    # start twice
    client.post("/tables/t1/start")
    assert client.post("/tables/t1/start").status_code == 409
    # bad Last-Event-ID
    resp = client.get("/tables/t1/stream", headers={"Last-Event-ID": "abc"})
    assert resp.status_code == 400


# ------------------------------------------------------------------- stream

def test_live_stream_is_complete_and_ordered(client):
    create_table(client, roll_delay_ms=2)
    client.post("/tables/t1/start")

    with client.stream("GET", "/tables/t1/stream") as resp:
        assert resp.headers["content-type"].startswith("text/event-stream")
        frames = list(iter_frames(resp))

    assert [f["id"] for f in frames] == list(range(len(frames)))
    assert frames[0]["event"] == "SessionStarted"
    assert frames[-1]["event"] == "SessionFinalized"
    for frame in frames:
        assert frame["data"]["type"] == frame["event"]
        assert frame["data"]["seq"] == frame["id"]
        assert frame["data"]["table_id"] == "t1"


def test_two_subscribers_see_identical_streams(client):
    create_table(client)
    client.post("/tables/t1/start")
    wait_for_state(client, "t1", "finished")

    def collect():
        with client.stream("GET", "/tables/t1/stream") as resp:
            return list(iter_frames(resp))

    first, second = collect(), collect()
    assert first == second
    assert first[-1]["event"] == "SessionFinalized"


def test_reconnect_with_last_event_id_is_gapless(client):
    create_table(client, roll_delay_ms=2, num_shooters=3)
    client.post("/tables/t1/start")

    head = []
    with client.stream("GET", "/tables/t1/stream") as resp:
        for frame in iter_frames(resp):
            head.append(frame)
            if len(head) == 10:
                break  # drop the connection mid-session

    tail = []
    with client.stream(
        "GET", "/tables/t1/stream",
        headers={"Last-Event-ID": str(head[-1]["id"])},
    ) as resp:
        tail = list(iter_frames(resp))

    ids = [f["id"] for f in head + tail]
    assert ids == list(range(len(ids))), "gap or duplicate across reconnect"
    assert (head + tail)[-1]["event"] == "SessionFinalized"


# ----------------------------------------------------------------- controls

def test_pause_resume_and_pace(client):
    create_table(client, roll_delay_ms=25, num_shooters=5)
    client.post("/tables/t1/start")

    deadline = time.time() + 20
    while client.get("/tables/t1").json()["session_rolls"] < 1:
        assert time.time() < deadline, "no rolls happened"
        time.sleep(0.02)

    assert client.post("/tables/t1/pause").status_code == 200
    time.sleep(0.1)  # let any in-flight roll land
    rolls_at_pause = client.get("/tables/t1").json()["session_rolls"]
    time.sleep(0.25)
    assert client.get("/tables/t1").json()["session_rolls"] == rolls_at_pause
    assert client.get("/tables/t1").json()["state"] == "paused"

    # invalid transitions
    assert client.post("/tables/t1/pause").status_code == 409

    # resume at TURBO and run out the session
    assert client.post(
        "/tables/t1/pace", json={"roll_delay_ms": 0}
    ).status_code == 200
    assert client.post("/tables/t1/resume").status_code == 200
    assert client.post("/tables/t1/resume").status_code == 409
    wait_for_state(client, "t1", "finished")


def test_step_advances_exactly_one_roll(client):
    create_table(client, roll_delay_ms=25, num_shooters=5)
    client.post("/tables/t1/start")

    # step is only valid while paused
    assert client.post("/tables/t1/step").status_code == 409

    deadline = time.time() + 20
    while client.get("/tables/t1").json()["session_rolls"] < 1:
        assert time.time() < deadline, "no rolls happened"
        time.sleep(0.02)
    assert client.post("/tables/t1/pause").status_code == 200
    time.sleep(0.1)  # let any in-flight roll land
    rolls_before = client.get("/tables/t1").json()["session_rolls"]

    for expected in range(rolls_before + 1, rolls_before + 4):
        resp = client.post("/tables/t1/step")
        assert resp.status_code == 200
        assert resp.json()["state"] == "paused"
        deadline = time.time() + 20
        while client.get("/tables/t1").json()["session_rolls"] < expected:
            assert time.time() < deadline, "step did not advance a roll"
            time.sleep(0.02)
        # exactly one roll per step — no free-run resumed underneath us
        time.sleep(0.15)
        assert client.get("/tables/t1").json()["session_rolls"] == expected
        assert client.get("/tables/t1").json()["state"] == "paused"


def test_step_ignores_the_configured_pace_delay(client):
    """A manual single-step Roll click should be instant — not throttled
    by whatever roll_delay_ms a prior Auto Play/Turbo run left configured.
    Continuous rolling (start/resume) still respects the pace; only the
    one roll step() lets through skips it."""
    create_table(client, roll_delay_ms=1500, num_shooters=5)
    client.post("/tables/t1/start")

    deadline = time.time() + 20
    while client.get("/tables/t1").json()["session_rolls"] < 1:
        assert time.time() < deadline, "no rolls happened"
        time.sleep(0.02)
    assert client.post("/tables/t1/pause").status_code == 200
    # The gate was never cleared before this pause() call (nothing else
    # clears it), so the loop was mid-sleep on the *next* roll's full
    # 1.5s pace the instant session_rolls hit 1 — unlike the small-delay
    # tests above, 0.1s isn't enough to let that in-flight roll land.
    time.sleep(1.7)
    rolls_before = client.get("/tables/t1").json()["session_rolls"]

    started = time.time()
    resp = client.post("/tables/t1/step")
    assert resp.status_code == 200

    deadline = time.time() + 1.0  # well under the configured 1.5s pace
    while client.get("/tables/t1").json()["session_rolls"] < rolls_before + 1:
        assert time.time() < deadline, "step waited for the full configured pace instead of skipping it"
        time.sleep(0.02)
    assert time.time() - started < 1.0


def test_max_rolls_and_stop(client):
    create_table(client, max_rolls=5)
    client.post("/tables/t1/start")
    snap = wait_for_state(client, "t1", "finished")
    assert snap["session_rolls"] == 5

    create_table(client, table_id="t2", roll_delay_ms=50, num_shooters=10)
    client.post("/tables/t2/start")
    assert client.post("/tables/t2/stop").status_code == 200
    assert client.get("/tables/t2").json()["state"] == "stopped"


# ---------------------------------------------------------- replay endpoints

def test_paged_events_walk_the_whole_session(client):
    create_table(client)
    client.post("/tables/t1/start")
    wait_for_state(client, "t1", "finished")
    total = client.get("/tables/t1/events?limit=0").json()["total"]

    seen = []
    after = -1
    while True:
        page = client.get(f"/tables/t1/events?after_seq={after}&limit=7").json()
        if not page["events"]:
            break
        seen.extend(e["seq"] for e in page["events"])
        after = page["next_after_seq"]
    assert seen == list(range(total))


def test_recording_events_page_matches_live_buffer(client):
    create_table(client)
    client.post("/tables/t1/start")
    wait_for_state(client, "t1", "finished")

    live = client.get("/tables/t1/events?limit=100000").json()
    name = client.get("/recordings").json()[0]["name"]
    recorded = client.get(f"/recordings/{name}/events?limit=100000").json()

    assert recorded["total"] == live["total"]
    assert recorded["events"] == live["events"]
    assert client.get("/recordings/notthere.jsonl/events").status_code == 404


# ----------------------------------------------------------------------- D6

def test_bare_bones_table_refuses_ats_over_http(client):
    lineup = [
        {"name": "ATS", "strategy": "AllTallSmall"},
        {"name": "Linus", "strategy": "Pass-Line"},
    ]
    create_table(
        client,
        players=lineup,
        house_rules={"ats_enabled": False},
        num_shooters=2,
    )
    client.post("/tables/t1/start")
    wait_for_state(client, "t1", "finished")

    events = client.get("/tables/t1/events?limit=100000").json()["events"]
    placed_types = {
        e["bet_type"] for e in events if e["type"] == "BetPlaced"
    }
    assert placed_types & {"All", "Tall", "Small"} == set()
    assert "Pass Line" in placed_types  # the rest of the table still plays
