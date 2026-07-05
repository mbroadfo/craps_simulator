"""The Observatory server (Phase 2, Step 1): FastAPI + SSE over the
Phase 1 event stream. The engine stays synchronous and untouched; this
package drives it (TableSession), fans its events out (Broadcaster),
and serves them (routes). The legacy manual-play API in craps/api is
separate and unchanged.
"""
