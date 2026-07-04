# Phase 2 Brief — The Observatory (DRAFT for review)

**Owner:** Mike Broadfoot (architect / decision maker)
**Status:** Draft — redline before any step is planned. No code until approved.
**Goal:** Watch the simulator. One or many live tables in the browser, each
rendering the Phase 1 event stream: felt, point puck, chips, dice, bankroll
sparklines, a leaderboard of realized-vs-theoretical edge, and dicer.io-style
roll distributions — plus full replay of any recorded session.

## What Phase 1 gives us (the load-bearing assumptions)

- The engine emits a complete, ordered event stream (`craps/events.py`):
  every roll, bet, resolution, transition, and bankroll movement is already
  a typed fact. **The UI is just another consumer.**
- Same seed → identical event stream. Replay and live are the same renderer
  fed from different sources.
- Strategies are pure `wants(view, memo) -> layout` functions — the
  prototype's own contract, so the UI vocabulary (layout, BetSpec, felt
  positions) maps 1:1 onto the engine's.
- Three machine-checked gates (bankroll parity, stats goldens, edge
  convergence) protect the math while the UI grows around it.

North-star design: `prototype/craps_observatory.jsx` ("The Rail") — in the
repo as a frozen reference. Its visual vocabulary (felt cards, box numbers
with the puck as an inverted tile, chip badges on place numbers, pip-accurate
dice, 120-point bankroll sparklines with a dashed break-even line, the
speed-control strip 1×/10×/100×/TURBO, and the leaderboard with max-drawdown
and realized-edge columns) is the Step 2–3 fidelity target. Its simplified
math is NOT — the real engine is the only source of game truth. Note the
prototype computes realized edge as pnl/wagered where "wagered" counts only
net new money placed; D5's definition (per amount bet at resolution) is the
correct one and will differ — expected, not a bug.

## Architecture decisions (the redline targets)

### D1 — Live transport: **SSE, not WebSocket**

Server-Sent Events for the live stream; plain REST for everything else.

Rationale: the felt is strictly one-directional — the browser only ever
*listens*. The interactive controls (start table, pace, pause, TURBO) are
low-frequency commands that fit ordinary `POST` endpoints; nothing needs a
bidirectional socket. SSE is plain HTTP: it rides through CloudFront and ALBs
without protocol upgrades (relevant when this follows The Reef onto AWS),
reconnects automatically with `Last-Event-ID` for gapless resume, and
FastAPI serves it with a bare `StreamingResponse` — no extra dependency.
WebSocket would buy us nothing here and cost operational complexity later.

### D2 — Replay: **recorded event log + the same renderer**

Sessions persist their event stream as JSONL (seq-numbered, one event per
line). Replay mode is a plain `GET` returning the log (paged); the front end
feeds it through the identical rendering path at user-controlled speed with
a scrubber. No server-side replay clock — the client owns playback time.

### D3 — Event serialization

One JSON envelope per event: `{seq, table_id, type, ...payload}`. Field
names come straight from the frozen dataclasses in `events.py` — the Python
event vocabulary IS the wire schema, documented in one place. Adding UI
needs (e.g. felt coordinates) happens client-side, not by fattening engine
events.

### D4 — Session orchestration

A `TableRunner` (async task) owns one engine instance and drives the
accept→roll→resolve loop at a controllable pace (roll delay 0ms "TURBO" to
~2s "live feel"). A `TableDirector` manages N runners. The engine itself
stays synchronous and untouched — runners call it exactly like
`simulation_runner.py` does today. Engine changes in Phase 2 are **additive
events only**, and all Phase 1 gates must stay green.

### D5 — Realized vs theoretical edge

Realized: from `BetResolved` amounts (already streaming). Theoretical: a
per-bet-type edge table (pass line 1.41%, field 2.78%, place 6/8 1.52%, ...)
weighted by each strategy's actual amount-bet mix — so composite strategies
(Iron Cross, Molly) get an honest blended benchmark rather than a hardcoded
number. Leaderboard converges toward zero delta if the engine's math is
right; that's the wizardofodds-grade check, live on screen.

## Scope, by step (each step = one pull, plan approved before code)

| Step | Scope | Gate |
| ---- | ----- | ---- |
| 0 | Event JSON serialization + JSONL session recorder + `TableRunner`/`TableDirector` (no HTTP yet) | Recorded log replays to identical stats; Phase 1 gates green |
| 1 | FastAPI: create/configure table sessions, SSE stream, pace/pause controls, replay + stats endpoints | Two browsers watch one table in sync; reconnect resumes gaplessly |
| 2 | Front end scaffold (Vite + React + TS + Tailwind) + single table card in the prototype's visual language: felt, point puck, chips, dice, per-player sparklines | Side-by-side with prototype: same information at a glance |
| 3 | The observatory: N-table grid, leaderboard (realized vs theoretical edge), dicer.io-style roll distribution panel | 6 tables at TURBO stay smooth; leaderboard math matches convergence numbers |
| 4 | Replay mode: load recorded session, scrubber, speed control | Replay of a recorded session renders identically to its live run |

## Non-goals (Phase 3+, explicitly out)

- AI strategy generation and tournaments (Phase 3 — the Strategy Lab)
- Auth, multi-user, persistence beyond session JSONL files
- Deployment/AWS (design stays CloudFront-compatible per D1, but no infra)
- Betting UI for humans — the observatory watches bots; it doesn't play

## Working agreement (carried from Phase 1)

Plan-first per step; Mike redlines before code. Engine behavior changes are
out of bounds — additive events only, existing gates always green. New
territory (TypeScript/React) gets its own quality bar: typecheck + lint +
component tests in CI alongside the Python jobs.

## Open questions for Mike

1. **Table configuration source** — reuse `ACTIVE_PLAYERS`-style config per
   table, or a small JSON body on `POST /tables` (recommended)?
2. **How many tables is the target?** Prototype showed 6; does the grid need
   to handle your "100k bots" ambitions in Phase 2, or is that Phase 3
   tournament territory (my assumption: Phase 3)?
3. **Roll distribution scope** — per-table, per-session aggregate, or both
   (prototype implied per-table; both is cheap if the events are logged)?
