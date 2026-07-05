"""TableDirector: the registry of live TableSessions (D4)."""
from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from craps.server.table_session import TableSession


class TableDirector:
    def __init__(self, sessions_dir: Union[str, Path] = "sessions") -> None:
        self.sessions_dir = Path(sessions_dir)
        self.tables: Dict[str, TableSession] = {}

    def create(self, table_id: Optional[str] = None, **kwargs: Any) -> TableSession:
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
