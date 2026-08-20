"""Per-table event fan-out (Phase 2, Step 1).

Subscribes to the engine bus the same way the recorder does (one
subscription to ``Event`` observes the full stream), keeps every
serialized envelope in memory indexed by seq, and feeds any number of
SSE subscribers through asyncio queues.

The runner's roll loop executes inside the event loop, so ``_on_event``
never races a subscriber — ``put_nowait`` is safe and ordering is the
bus's deterministic publish order. ``listen(after_seq)`` is what makes
``Last-Event-ID`` resume gapless: history replays from the buffer, the
seq guard drops the overlap with anything queued meanwhile.
"""
from __future__ import annotations
import asyncio
from collections import deque
from itertools import islice
from typing import Any, AsyncGenerator, Deque, Dict, List, Optional

from craps.events import Event, EventBus, SessionFinalized
from craps.serialization import serialize_event

_CLOSE: Optional[Dict[str, Any]] = None  # queue sentinel

#: Cap on envelopes retained per table. This buffer used to grow for the
#: life of the process, which was fine on a workstation and is not fine
#: in a 1 GB container. A normal 10-shooter session produces low
#: thousands, so the cap only bites a pathological one (a huge
#: num_shooters, or Turbo left running unattended) — exactly the case
#: that would otherwise OOM the box. Replay deeper than the cap comes
#: from the recorded .jsonl, which is never trimmed.
MAX_BUFFERED_EVENTS = 20_000


class Broadcaster:
    def __init__(self, table_id: str) -> None:
        self.table_id = table_id
        #: The most recent MAX_BUFFERED_EVENTS envelopes, oldest first.
        #: Bounded, so seq is NO LONGER the index — use _first_seq to
        #: convert. maxlen makes eviction O(1); trimming a list from the
        #: front would be O(n) per event at the cap.
        self.buffer: Deque[Dict[str, Any]] = deque(maxlen=MAX_BUFFERED_EVENTS)
        #: Next seq to hand out. Monotonic for the session's life —
        #: never rewound by trimming, so ids stay stable for
        #: Last-Event-ID resume.
        self._next_seq = 0
        self.finished = False
        self._queues: List["asyncio.Queue[Optional[Dict[str, Any]]]"] = []

    def subscribe(self, bus: EventBus) -> None:
        bus.subscribe(Event, self._on_event)

    @property
    def next_seq(self) -> int:
        return self._next_seq

    @property
    def _first_seq(self) -> int:
        """seq of buffer[0]. Derived rather than tracked separately, so
        it can't drift out of step with what the deque actually holds."""
        return self._next_seq - len(self.buffer)

    def _slice_from(self, after_seq: int, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Envelopes with seq > after_seq, oldest first, at most `limit`.

        Materialized (not a lazy islice) on purpose: callers yield
        across await points, and the deque can be appended to in
        between — iterating it lazily would raise "deque mutated during
        iteration". Requests for seqs already trimmed away start from
        the oldest still held.
        """
        start = max(0, after_seq + 1 - self._first_seq)
        stop = None if limit is None else start + max(0, limit)
        return list(islice(self.buffer, start, stop))

    def events_after(self, after_seq: int, limit: int) -> List[Dict[str, Any]]:
        """Paged history for the /events endpoint."""
        return self._slice_from(after_seq, limit)

    def _on_event(self, event: Event) -> None:
        envelope = serialize_event(event, seq=self._next_seq, table_id=self.table_id)
        self._next_seq += 1
        self.buffer.append(envelope)  # maxlen drops the oldest for us
        for queue in list(self._queues):
            queue.put_nowait(envelope)
        if isinstance(event, SessionFinalized):
            self.close()

    def close(self) -> None:
        """End all live listens; the buffer stays readable."""
        if not self.finished:
            self.finished = True
            for queue in list(self._queues):
                queue.put_nowait(_CLOSE)

    async def listen(
        self, after_seq: int = -1, keepalive: Optional[float] = None
    ) -> AsyncGenerator[Optional[Dict[str, Any]], None]:
        """Yield every envelope with seq > after_seq: buffered history
        first, then live events, ending when the session finalizes.

        With ``keepalive`` set, yields ``None`` whenever that many
        seconds pass with no event, so the caller can emit an SSE
        comment frame. A *paused* table publishes nothing at all, and
        proxies (Cloudflare's is ~100s) drop a connection that goes
        quiet — without a heartbeat the stream dies mid-pause and the
        felt silently stops updating. ``None`` (the default) preserves
        the original block-forever behavior for non-SSE callers.
        """
        queue: "asyncio.Queue[Optional[Dict[str, Any]]]" = asyncio.Queue()
        # Register before replaying history so nothing published in
        # between is missed; the seq guard below drops the overlap.
        self._queues.append(queue)
        try:
            last = after_seq
            for envelope in self._slice_from(after_seq):
                yield envelope
                last = envelope["seq"]
            if self.finished:
                return
            while True:
                if keepalive is None:
                    item = await queue.get()
                else:
                    try:
                        item = await asyncio.wait_for(queue.get(), timeout=keepalive)
                    except asyncio.TimeoutError:
                        yield None
                        continue
                if item is None:  # _CLOSE sentinel
                    return
                if item["seq"] > last:
                    yield item
                    last = item["seq"]
        finally:
            self._queues.remove(queue)
