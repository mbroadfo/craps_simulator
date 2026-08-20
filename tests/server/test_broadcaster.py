"""Broadcaster keepalive behavior.

The SSE stream has to survive an idle stretch: a *paused* table
publishes nothing, and proxies (Cloudflare's is ~100s) drop a
connection that goes silent. Without a heartbeat the stream dies
mid-pause and the felt just stops updating with no error anywhere.

These drive the async generator directly rather than through
TestClient — there's no async test plugin in the dev deps, and the
keepalive is a Broadcaster concern, not an HTTP one.
"""
import asyncio

import craps.server.broadcaster as broadcaster_module
from craps.events import BetsRequested
from craps.server.broadcaster import Broadcaster

# Short enough to keep the suite fast, long enough not to be flaky on a
# loaded CI box.
TICK = 0.02


def test_listen_yields_keepalives_while_no_events_arrive():
    async def scenario():
        broadcaster = Broadcaster("t1")
        stream = broadcaster.listen(keepalive=TICK)
        out = []
        for _ in range(3):
            out.append(await stream.__anext__())
        await stream.aclose()
        return out

    assert asyncio.run(scenario()) == [None, None, None]


def test_keepalive_does_not_swallow_the_next_real_event():
    """The idle timeout cancels a pending queue.get(); this proves that
    cancellation can't drop an event that lands around the same time."""

    async def scenario():
        broadcaster = Broadcaster("t1")
        stream = broadcaster.listen(keepalive=TICK)
        assert await stream.__anext__() is None  # idle first

        broadcaster._on_event(BetsRequested())
        envelope = await stream.__anext__()
        await stream.aclose()
        return envelope

    envelope = asyncio.run(scenario())
    assert envelope is not None
    assert envelope["type"] == "BetsRequested"
    assert envelope["seq"] == 0


def test_without_keepalive_listen_still_blocks_for_a_real_event():
    """Default (None) must keep the original block-until-published
    behavior — no None values injected into non-SSE consumers."""

    async def scenario():
        broadcaster = Broadcaster("t1")
        stream = broadcaster.listen()

        async def publish_soon():
            await asyncio.sleep(TICK * 2)
            broadcaster._on_event(BetsRequested())

        task = asyncio.create_task(publish_soon())
        envelope = await stream.__anext__()
        await task
        await stream.aclose()
        return envelope

    envelope = asyncio.run(scenario())
    assert envelope is not None
    assert envelope["type"] == "BetsRequested"


def _publish(broadcaster, count):
    for _ in range(count):
        broadcaster._on_event(BetsRequested())


def test_buffer_is_capped_but_seq_keeps_climbing(monkeypatch):
    """The buffer used to grow for the whole process lifetime, which is
    an OOM on a small container. Trimming must not rewind seq — ids have
    to stay stable for Last-Event-ID resume."""
    monkeypatch.setattr(broadcaster_module, "MAX_BUFFERED_EVENTS", 10)
    broadcaster = Broadcaster("t1")

    _publish(broadcaster, 25)

    assert len(broadcaster.buffer) == 10  # bounded
    assert broadcaster.next_seq == 25  # but every event still got an id
    assert [e["seq"] for e in broadcaster.buffer] == list(range(15, 25))


def test_events_after_stays_correct_once_the_buffer_has_trimmed(monkeypatch):
    """seq is no longer the buffer index, so paging has to offset by
    how much was dropped — off-by-one here would silently replay or skip
    events on every reconnect."""
    monkeypatch.setattr(broadcaster_module, "MAX_BUFFERED_EVENTS", 10)
    broadcaster = Broadcaster("t1")
    _publish(broadcaster, 25)

    page = broadcaster.events_after(19, limit=3)
    assert [e["seq"] for e in page] == [20, 21, 22]

    # Asking for everything still held.
    assert [e["seq"] for e in broadcaster.events_after(-1, limit=100)] == list(
        range(15, 25)
    )

    # Asking past the end yields nothing rather than wrapping around.
    assert broadcaster.events_after(24, limit=5) == []


def test_listen_replays_from_the_oldest_retained_event_after_trimming(monkeypatch):
    """A client resuming from a seq that's been trimmed away can't be
    served exactly; it must get the oldest still held, not an empty
    replay or an IndexError."""
    monkeypatch.setattr(broadcaster_module, "MAX_BUFFERED_EVENTS", 10)

    async def scenario():
        broadcaster = Broadcaster("t1")
        _publish(broadcaster, 25)
        stream = broadcaster.listen(after_seq=2)  # long since trimmed
        first = await stream.__anext__()
        await stream.aclose()
        return first

    first = asyncio.run(scenario())
    assert first is not None
    assert first["seq"] == 15


def test_listen_stops_when_the_session_closes():
    """A finalized session must end the stream even with keepalive on,
    rather than heartbeating forever."""

    async def scenario():
        broadcaster = Broadcaster("t1")
        stream = broadcaster.listen(keepalive=TICK)
        assert await stream.__anext__() is None

        broadcaster.close()
        try:
            await stream.__anext__()
        except StopAsyncIteration:
            return "stopped"
        return "kept going"

    assert asyncio.run(scenario()) == "stopped"
