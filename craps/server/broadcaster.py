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
from typing import Any, AsyncIterator, Dict, List, Optional

from craps.events import Event, EventBus, SessionFinalized
from craps.serialization import serialize_event

_CLOSE: Optional[Dict[str, Any]] = None  # queue sentinel


class Broadcaster:
    def __init__(self, table_id: str) -> None:
        self.table_id = table_id
        #: buffer[i] is the envelope with seq == i, from session start.
        self.buffer: List[Dict[str, Any]] = []
        self.finished = False
        self._queues: List["asyncio.Queue[Optional[Dict[str, Any]]]"] = []

    def subscribe(self, bus: EventBus) -> None:
        bus.subscribe(Event, self._on_event)

    @property
    def next_seq(self) -> int:
        return len(self.buffer)

    def _on_event(self, event: Event) -> None:
        envelope = serialize_event(event, seq=len(self.buffer), table_id=self.table_id)
        self.buffer.append(envelope)
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

    async def listen(self, after_seq: int = -1) -> AsyncIterator[Dict[str, Any]]:
        """Yield every envelope with seq > after_seq: buffered history
        first, then live events, ending when the session finalizes."""
        queue: "asyncio.Queue[Optional[Dict[str, Any]]]" = asyncio.Queue()
        # Register before replaying history so nothing published in
        # between is missed; the seq guard below drops the overlap.
        self._queues.append(queue)
        try:
            last = after_seq
            for envelope in self.buffer[after_seq + 1:]:
                yield envelope
                last = envelope["seq"]
            if self.finished:
                return
            while True:
                item = await queue.get()
                if item is None:  # _CLOSE sentinel
                    return
                if item["seq"] > last:
                    yield item
                    last = item["seq"]
        finally:
            self._queues.remove(queue)
