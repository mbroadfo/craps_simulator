"""TableDirector: the registry of live TableSessions (D4)."""
from __future__ import annotations
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from craps.server.table_session import TableSession

#: How long a finished/stopped table stays queryable (stats, paged
#: events, the just-played session's replay) before eviction.
FINISHED_TABLE_TTL_SECONDS = 3600.0

#: Hard ceiling on registry size. Each table pins its whole event buffer
#: plus engine state in memory and nothing ever removed one, so a
#: long-lived process accumulated every table ever created — fine on a
#: workstation, an OOM in a 1 GB container.
MAX_TABLES = 20

#: States from which a table can no longer roll, so it's safe to drop.
TERMINAL_STATES = frozenset({"finished", "stopped"})


class TableLimitReached(RuntimeError):
    """Raised when no table slot can be freed — surfaces as HTTP 503."""


class TableDirector:
    def __init__(self, sessions_dir: Union[str, Path] = "sessions") -> None:
        self.sessions_dir = Path(sessions_dir)
        self.tables: Dict[str, TableSession] = {}

    def _finished_oldest_first(self) -> List[Tuple[float, str]]:
        return sorted(
            (session.ended_at or 0.0, table_id)
            for table_id, session in self.tables.items()
            if session.state in TERMINAL_STATES
        )

    def prune(self) -> List[str]:
        """Drop finished tables past their TTL, then — if still at the
        cap — the oldest finished ones. Running/paused tables are never
        evicted; a full registry of live tables refuses new ones instead
        (see create). Returns the evicted ids."""
        now = time.monotonic()
        finished = self._finished_oldest_first()
        evicted: List[str] = []

        for ended_at, table_id in list(finished):
            if now - ended_at >= FINISHED_TABLE_TTL_SECONDS:
                del self.tables[table_id]
                finished.remove((ended_at, table_id))
                evicted.append(table_id)

        while len(self.tables) >= MAX_TABLES and finished:
            _, table_id = finished.pop(0)
            del self.tables[table_id]
            evicted.append(table_id)

        return evicted

    def create(self, table_id: Optional[str] = None, **kwargs: Any) -> TableSession:
        self.prune()
        if len(self.tables) >= MAX_TABLES:
            raise TableLimitReached(
                f"{MAX_TABLES} tables already active; stop one before creating another"
            )
        if table_id is None:
            n = 1
            while f"table-{n}" in self.tables:
                n += 1
            table_id = f"table-{n}"
        if table_id in self.tables:
            raise ValueError(f"table {table_id!r} already exists")
        session = TableSession(
            table_id=table_id, sessions_dir=self.sessions_dir, **kwargs
        )
        self.tables[table_id] = session
        return session

    def get(self, table_id: str) -> Optional[TableSession]:
        return self.tables.get(table_id)

    def list(self) -> List[Dict[str, Any]]:
        return [session.snapshot() for session in self.tables.values()]

    async def shutdown(self) -> None:
        for session in self.tables.values():
            await session.stop()
