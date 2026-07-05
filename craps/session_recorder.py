"""JSONL session recorder (Phase 2, Step 0).

A consumer that subscribes to the full event stream (the bus dispatches
by MRO, so one subscription to ``Event`` observes everything) and writes
one wire envelope per line to ``sessions/<table_id>_<timestamp>.jsonl``
(D2). ``seq`` is assigned here, monotonically from 0 per session — the
engine knows nothing about sequence numbers or files.

Attach before ``setup_session()`` so the ``SessionStarted`` event
published at the end of setup is captured. The file closes itself on
``SessionFinalized``; ``close()`` is the fallback for interrupted runs.
"""
from __future__ import annotations
import json
from datetime import datetime
from pathlib import Path
from typing import IO, Iterator, Optional, Tuple, Union

from craps.events import Event, EventBus, SessionFinalized
from craps.serialization import deserialize_event, serialize_event


class SessionRecorder:
    def __init__(self, table_id: str, sessions_dir: Union[str, Path] = "sessions") -> None:
        self.table_id = table_id
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        self.path = Path(sessions_dir) / f"{table_id}_{timestamp}.jsonl"
        self._file: Optional[IO[str]] = None  # opened lazily on first event
        self._seq = 0

    def subscribe(self, bus: EventBus) -> None:
        bus.subscribe(Event, self._on_event)

    def _on_event(self, event: Event) -> None:
        if self._file is None:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self._file = self.path.open("w", encoding="utf-8")
        envelope = serialize_event(event, seq=self._seq, table_id=self.table_id)
        self._file.write(json.dumps(envelope, separators=(",", ":")) + "\n")
        self._seq += 1
        if isinstance(event, SessionFinalized):
            self.close()

    def close(self) -> None:
        if self._file is not None:
            self._file.close()
            self._file = None


def load_session(path: Union[str, Path]) -> Iterator[Tuple[int, str, Event]]:
    """Yield ``(seq, table_id, event)`` for each line of a recorded session."""
    with Path(path).open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield deserialize_event(json.loads(line))
