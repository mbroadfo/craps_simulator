# syntax=docker/dockerfile:1
#
# One image serving both the API and the built SPA. The frontend calls
# bare root-relative paths (/tables, new EventSource('/tables/x/stream'))
# with no base URL, so it can only work same-origin — hence one
# container rather than a separate static host.

# ---- Stage 1: build the SPA -------------------------------------------------
FROM node:22-slim AS web

WORKDIR /web
# Copy manifests first so `npm ci` is cached until dependencies change.
COPY web/package.json web/package-lock.json ./
RUN npm ci

COPY web/ ./
# `npm run build` is `tsc -b && vite build`, so a type error fails the
# image build rather than shipping broken output.
RUN npm run build


# ---- Stage 2: runtime -------------------------------------------------------
FROM python:3.13-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    # matplotlib is only reachable from CLI charting (imported lazily in
    # craps/visualizer.py), but if anything does reach it there's no
    # display here.
    MPLBACKEND=agg \
    PORT=8000 \
    CRAPS_STATIC_DIR=/app/static

WORKDIR /app

# config.py sits at the repo root but is imported by the craps package;
# pyproject's py-modules entry makes `pip install .` carry it along.
COPY pyproject.toml config.py ./
COPY craps/ ./craps/
RUN pip install --no-cache-dir .

COPY --from=web /web/dist/ /app/static/

# Non-root, with the two directories the engine writes to at runtime:
# PlayByPlay unconditionally does os.makedirs("output") on construction,
# and SessionRecorder writes sessions/<table>.jsonl per table.
RUN useradd --create-home --uid 10001 craps \
    && mkdir -p /app/sessions /app/output \
    && chown -R craps:craps /app
USER craps

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=20s --retries=3 \
    CMD python -c "import os,urllib.request; urllib.request.urlopen('http://127.0.0.1:%s/health' % os.environ.get('PORT','8000'), timeout=2)"

# Shell form so $PORT is expanded; exec so uvicorn is PID 1 and gets
# SIGTERM directly (Fargate stops the task by signalling PID 1, and the
# app's lifespan hook needs that to finalize running tables).
CMD ["sh", "-c", "exec uvicorn craps.server.app:app --host 0.0.0.0 --port ${PORT:-8000}"]
