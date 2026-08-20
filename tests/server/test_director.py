"""TableDirector eviction.

The registry had no delete path at all: every table ever created stayed
in memory, pinning its engine state and its whole event buffer, for the
life of the process. Fine on a workstation that gets restarted; an OOM
in a long-lived 1 GB container.

prune() is exercised directly with stub sessions — building real
TableSessions would drag in the engine for what is purely a
retention-policy question.
"""
import time

import pytest

import craps.server.director as director_module
from craps.server.director import TableDirector, TableLimitReached

LINEUP = [("Linus", "Pass-Line")]


class _StubSession:
    """Only what prune() looks at."""

    def __init__(self, state, ended_at=None):
        self.state = state
        self.ended_at = ended_at


@pytest.fixture
def director(tmp_path):
    return TableDirector(sessions_dir=tmp_path / "sessions")


def test_prune_drops_finished_tables_past_their_ttl(director, monkeypatch):
    monkeypatch.setattr(director_module, "FINISHED_TABLE_TTL_SECONDS", 60.0)
    now = time.monotonic()
    director.tables["old"] = _StubSession("finished", ended_at=now - 120)
    director.tables["recent"] = _StubSession("finished", ended_at=now - 5)

    evicted = director.prune()

    assert evicted == ["old"]
    assert set(director.tables) == {"recent"}


def test_prune_never_evicts_a_table_that_can_still_roll(director, monkeypatch):
    """Age alone must not evict something live — a paused table may sit
    idle far longer than the TTL while someone reads the felt."""
    monkeypatch.setattr(director_module, "FINISHED_TABLE_TTL_SECONDS", 0.0)
    ancient = time.monotonic() - 10_000
    director.tables["running"] = _StubSession("running", ended_at=None)
    director.tables["paused"] = _StubSession("paused", ended_at=None)
    director.tables["created"] = _StubSession("created", ended_at=None)
    director.tables["done"] = _StubSession("stopped", ended_at=ancient)

    evicted = director.prune()

    assert evicted == ["done"]
    assert set(director.tables) == {"running", "paused", "created"}


def test_prune_evicts_oldest_finished_first_when_at_the_cap(director, monkeypatch):
    """Under the cap but within TTL, the oldest finished table gives way
    so a new one can be created."""
    monkeypatch.setattr(director_module, "MAX_TABLES", 3)
    monkeypatch.setattr(director_module, "FINISHED_TABLE_TTL_SECONDS", 10_000.0)
    now = time.monotonic()
    director.tables["a"] = _StubSession("finished", ended_at=now - 30)
    director.tables["b"] = _StubSession("finished", ended_at=now - 10)
    director.tables["c"] = _StubSession("running", ended_at=None)

    evicted = director.prune()

    assert evicted == ["a"]  # oldest finished, not the running one
    assert set(director.tables) == {"b", "c"}


def test_create_refuses_when_every_slot_holds_a_live_table(director, monkeypatch):
    """Nothing is evictable, so creation must fail loudly rather than
    grow the registry without bound."""
    monkeypatch.setattr(director_module, "MAX_TABLES", 2)
    director.tables["a"] = _StubSession("running", ended_at=None)
    director.tables["b"] = _StubSession("paused", ended_at=None)

    with pytest.raises(TableLimitReached):
        director.create(table_id="c", players=LINEUP)

    assert set(director.tables) == {"a", "b"}


def test_create_makes_room_by_evicting_a_finished_table(director, monkeypatch):
    monkeypatch.setattr(director_module, "MAX_TABLES", 2)
    monkeypatch.setattr(director_module, "FINISHED_TABLE_TTL_SECONDS", 10_000.0)
    director.tables["done"] = _StubSession("finished", ended_at=time.monotonic() - 5)
    director.tables["live"] = _StubSession("running", ended_at=None)

    session = director.create(table_id="fresh", players=LINEUP)

    assert session.table_id == "fresh"
    assert set(director.tables) == {"live", "fresh"}


def test_create_still_rejects_a_duplicate_id(director):
    director.create(table_id="t1", players=LINEUP)
    with pytest.raises(ValueError):
        director.create(table_id="t1", players=LINEUP)
