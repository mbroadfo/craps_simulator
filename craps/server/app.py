"""Observatory app factory (Phase 2, Step 1).

Run it with:  uvicorn craps.server.app:app --reload
Tests build isolated apps via create_app(sessions_dir=tmp_path).

In a deployed container this same app also serves the built SPA, so
the whole thing is one origin (see _static_dir below) — the frontend
calls bare paths like /tables and new EventSource('/tables/x/stream')
with no base URL, so it can only ever work same-origin.
"""
from __future__ import annotations
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator, Dict, Optional, Union

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from craps.server.director import TableDirector
from craps.server.routes import recordings_router, tables_router


def _static_dir() -> Optional[Path]:
    """Where the built SPA lives, or None if it hasn't been built.

    CRAPS_STATIC_DIR is what the container sets; the fallback is the
    repo layout (<root>/web/dist) so a local `npm run build` is served
    by a plain `uvicorn craps.server.app:app` too. Returning None when
    there's no build keeps `npm run dev` (Vite proxying to this server)
    and the test suite working unchanged.
    """
    override = os.environ.get("CRAPS_STATIC_DIR")
    candidate = (
        Path(override)
        if override
        else Path(__file__).resolve().parents[2] / "web" / "dist"
    )
    return candidate if (candidate / "index.html").is_file() else None


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

    @app.get("/health", tags=["Ops"])
    async def health() -> Dict[str, str]:
        """Liveness probe for the ECS health check and the Cloudflare
        waker, which polls this to decide when the container is ready."""
        return {"status": "ok"}

    app.include_router(tables_router)
    app.include_router(recordings_router)

    # Mounted last so /tables, /recordings, /health and FastAPI's own
    # /docs routes all match first — Starlette resolves in insertion
    # order, and this mount would otherwise swallow everything under /.
    # html=True serves index.html for "/" and 404s unknown paths, which
    # is right here: the SPA has no client-side router to fall back for.
    static = _static_dir()
    if static is not None:
        app.mount("/", StaticFiles(directory=static, html=True), name="spa")
    return app


app = create_app()
