"""Idle-shutdown policy.

The cost model depends on the task sleeping, but sleeping at the wrong
moment kills a session someone is watching -- and during autoplay the
browser sends NO requests at all, because everything arrives on one
long-lived SSE stream. So "no recent requests" alone is the wrong signal.
"""
import time

from craps.server.idle_shutdown import ActivityTracker, watchdog_from_env


def test_a_fresh_tracker_is_not_idle():
    assert not ActivityTracker().is_idle(threshold_seconds=60)


def test_goes_idle_once_the_threshold_passes_with_no_streams():
    t = ActivityTracker()
    t.last_request_at = time.monotonic() - 120
    assert t.is_idle(threshold_seconds=60)


def test_an_open_stream_blocks_shutdown_however_long_it_has_been_quiet():
    """The regression that matters: an autoplay session generates no HTTP
    requests, so a request-timestamp-only check would sleep the service out
    from under a felt that is actively rolling."""
    t = ActivityTracker()
    t.stream_opened()
    t.last_request_at = time.monotonic() - 86_400  # a day of no requests

    assert not t.is_idle(threshold_seconds=60)


def test_closing_the_last_stream_re_arms_the_countdown():
    t = ActivityTracker()
    t.stream_opened()
    t.stream_closed()
    t.last_request_at = time.monotonic() - 120

    assert t.is_idle(threshold_seconds=60)


def test_stream_counting_handles_overlapping_viewers():
    t = ActivityTracker()
    t.stream_opened()
    t.stream_opened()
    t.stream_closed()
    t.last_request_at = time.monotonic() - 120

    assert not t.is_idle(threshold_seconds=60)  # one viewer still connected
    t.stream_closed()
    t.last_request_at = time.monotonic() - 120
    assert t.is_idle(threshold_seconds=60)


def test_stream_count_never_goes_negative():
    """A close without a matching open (a torn-down connection replayed on
    restart, say) must not drive the count below zero and wedge the service
    permanently awake."""
    t = ActivityTracker()
    t.stream_closed()
    t.stream_closed()
    assert t.active_streams == 0
    t.last_request_at = time.monotonic() - 120
    assert t.is_idle(threshold_seconds=60)


def test_watchdog_is_disabled_without_ecs_env(monkeypatch):
    """Local dev, tests and the CLI must never self-terminate."""
    monkeypatch.delenv("CRAPS_ECS_CLUSTER", raising=False)
    monkeypatch.delenv("CRAPS_ECS_SERVICE", raising=False)
    assert watchdog_from_env(ActivityTracker()) is None


def test_watchdog_is_disabled_when_minutes_is_zero(monkeypatch):
    monkeypatch.setenv("CRAPS_ECS_CLUSTER", "crapsim")
    monkeypatch.setenv("CRAPS_ECS_SERVICE", "crapsim")
    monkeypatch.setenv("CRAPS_IDLE_SHUTDOWN_MINUTES", "0")
    assert watchdog_from_env(ActivityTracker()) is None


def test_health_checks_do_not_count_as_activity(tmp_path):
    """Regression for a bug found only by reading the deployed container's
    logs: ECS runs the health check from inside the task, hitting /health
    every 30s. Counting that as activity resets the idle timer forever, so
    the service never sleeps and the cost model quietly collapses.
    """
    from fastapi.testclient import TestClient

    from craps.server.app import create_app

    app = create_app(sessions_dir=tmp_path / "sessions")
    with TestClient(app) as client:
        tracker = app.state.activity
        tracker.last_request_at = time.monotonic() - 3600

        assert client.get("/health").status_code == 200
        assert tracker.is_idle(threshold_seconds=60), "health check reset the idle timer"

        assert client.get("/tables").status_code == 200
        assert not tracker.is_idle(threshold_seconds=60), "real request should count"
