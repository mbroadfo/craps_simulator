"""Observatory app factory (Phase 2, Step 1).

Run it with:  uvicorn craps.server.app:app --reload
Tests build isolated apps via create_app(sessions_dir=tmp_path).
"""
from __future__ import annotations
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator, Union

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from craps.server.director import TableDirector
from craps.server.routes import recordings_router, tables_router


def create_app(sessions_dir: Union[str, Path] = "sessions") -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        yield
        await app.state.director.shutdown()

    app = FastAPI(title="Craps Observatory API", lifespan=lifespan)
    app.state.director = TableDirector(sessions_dir=sessions_dir)

    app.add_middleware(
        CORSMiddleware,
        # Vite's default port (5173) auto-increments past whatever's
        # already listening (5174, 5175, ...) when this machine has
        # other dev servers running — a fixed allowlist just breaks
        # every time that happens. Matching any localhost port is
        # still scoped to local dev (never 0.0.0.0/a real origin), so
        # it doesn't loosen anything that mattered.
        allow_origin_regex=r"http://localhost:\d+",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(tables_router)
    app.include_router(recordings_router)
    return app


app = create_app()
