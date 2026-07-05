"""Observatory endpoints (Phase 2, Step 1).

Live transport is SSE (D1): the felt only listens, controls are plain
POSTs. Replay is a paged GET over the recorded log (D2) — no
server-side playback clock.
"""
from __future__ import annotations
import json
from typing import Any, AsyncIterator, Dict, List

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from craps.house_rules import HouseRules
from craps.lineup import PlayerLineup
from craps.play_by_play import PlayByPlay
from craps.rules_engine import RulesEngine
from craps.server.director import TableDirector
from craps.server.schemas import CreateTableRequest, PaceRequest
from craps.server.table_session import TableSession

tables_router = APIRouter(prefix="/tables", tags=["Observatory"])
recordings_router = APIRouter(prefix="/recordings", tags=["Recordings"])

#: Strategy names PlayerLineup can seat — the create-table vocabulary.
VALID_STRATEGIES = frozenset(
    PlayerLineup(HouseRules({}), None, PlayByPlay(), RulesEngine()).all_strategies
)

SSE_HEADERS = {
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "X-Accel-Buffering": "no",
}


def _director(request: Request) -> TableDirector:
    director: TableDirector = request.app.state.director
    return director


def _session(request: Request, table_id: str) -> TableSession:
    session = _director(request).get(table_id)
    if session is None:
        raise HTTPException(status_code=404, detail=f"No table {table_id!r}")
    return session


@tables_router.post("", status_code=201)
async def create_table(request: Request, body: CreateTableRequest) -> Dict[str, Any]:
    unknown = [p.strategy for p in body.players if p.strategy not in VALID_STRATEGIES]
    if unknown:
        raise HTTPException(
            status_code=422,
            detail=f"Unknown strategies {unknown}; valid: {sorted(VALID_STRATEGIES)}",
        )
    try:
        session = _director(request).create(
            table_id=body.table_id,
            players=[(p.name, p.strategy) for p in body.players],
            house_rules=body.house_rules,
            roll_delay_ms=body.roll_delay_ms,
            max_shooters=body.num_shooters,
            max_rolls=body.max_rolls,
            dice_seed=body.dice_seed,
            record=body.record,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return session.snapshot()


@tables_router.get("")
async def list_tables(request: Request) -> List[Dict[str, Any]]:
    return _director(request).list()


@tables_router.get("/{table_id}")
async def get_table(request: Request, table_id: str) -> Dict[str, Any]:
    return _session(request, table_id).snapshot()


@tables_router.post("/{table_id}/start")
async def start_table(request: Request, table_id: str) -> Dict[str, Any]:
    session = _session(request, table_id)
    try:
        session.start()
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return session.snapshot()


@tables_router.post("/{table_id}/pause")
async def pause_table(request: Request, table_id: str) -> Dict[str, Any]:
    session = _session(request, table_id)
    try:
        session.pause()
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return session.snapshot()


@tables_router.post("/{table_id}/resume")
async def resume_table(request: Request, table_id: str) -> Dict[str, Any]:
    session = _session(request, table_id)
    try:
        session.resume()
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return session.snapshot()


@tables_router.post("/{table_id}/pace")
async def set_pace(request: Request, table_id: str, body: PaceRequest) -> Dict[str, Any]:
    session = _session(request, table_id)
    session.set_pace(body.roll_delay_ms)
    return session.snapshot()


@tables_router.post("/{table_id}/stop")
async def stop_table(request: Request, table_id: str) -> Dict[str, Any]:
    session = _session(request, table_id)
    await session.stop()
    return session.snapshot()


@tables_router.get("/{table_id}/stats")
async def table_stats(request: Request, table_id: str) -> Dict[str, Any]:
    return _session(request, table_id).stats_snapshot()


@tables_router.get("/{table_id}/events")
async def table_events(
    request: Request, table_id: str, after_seq: int = -1, limit: int = 1000
) -> Dict[str, Any]:
    """Paged event log for the live/just-finished session (D2)."""
    session = _session(request, table_id)
    buffer = session.broadcaster.buffer
    page = buffer[after_seq + 1 : after_seq + 1 + max(0, limit)]
    return {
        "table_id": table_id,
        "events": page,
        "next_after_seq": page[-1]["seq"] if page else after_seq,
        "total": len(buffer),
        "finished": session.broadcaster.finished,
    }


@tables_router.get("/{table_id}/stream")
async def stream_table(request: Request, table_id: str) -> StreamingResponse:
    """SSE live stream (D1). Reconnect with Last-Event-ID resumes
    gaplessly from the seq after the one the client last saw."""
    session = _session(request, table_id)
    last_event_id = request.headers.get("last-event-id")
    after_seq = -1
    if last_event_id is not None:
        try:
            after_seq = int(last_event_id)
        except ValueError as exc:
            raise HTTPException(
                status_code=400, detail=f"Bad Last-Event-ID {last_event_id!r}"
            ) from exc

    async def event_source() -> AsyncIterator[str]:
        async for envelope in session.broadcaster.listen(after_seq):
            data = json.dumps(envelope, separators=(",", ":"))
            yield f"id: {envelope['seq']}\nevent: {envelope['type']}\ndata: {data}\n\n"

    return StreamingResponse(
        event_source(), media_type="text/event-stream", headers=SSE_HEADERS
    )


@recordings_router.get("")
async def list_recordings(request: Request) -> List[Dict[str, Any]]:
    sessions_dir = _director(request).sessions_dir
    if not sessions_dir.is_dir():
        return []
    return sorted(
        (
            {
                "name": path.name,
                "size_bytes": path.stat().st_size,
                "modified": path.stat().st_mtime,
            }
            for path in sessions_dir.glob("*.jsonl")
        ),
        key=lambda entry: str(entry["name"]),
    )


@recordings_router.get("/{name}/events")
async def recording_events(
    request: Request, name: str, after_seq: int = -1, limit: int = 1000
) -> Dict[str, Any]:
    """Paged raw envelopes from a recorded JSONL session (D2/Step 4)."""
    sessions_dir = _director(request).sessions_dir
    path = (sessions_dir / name).resolve()
    if (
        path.suffix != ".jsonl"
        or path.parent != sessions_dir.resolve()
        or not path.is_file()
    ):
        raise HTTPException(status_code=404, detail=f"No recording {name!r}")
    events: List[Dict[str, Any]] = []
    total = 0
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            total += 1
            envelope = json.loads(line)
            if envelope["seq"] > after_seq and len(events) < max(0, limit):
                events.append(envelope)
    return {
        "name": name,
        "events": events,
        "next_after_seq": events[-1]["seq"] if events else after_seq,
        "total": total,
    }
