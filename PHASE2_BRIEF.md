# Phase 2 Brief — The Observatory

**Owner:** Mike Broadfoot (architect / decision maker)
**Status:** Approved (pull #9) + table-fidelity amendment (Mike, 2026-07-04).
**Goal:** Watch the simulator. A **faithful, beautiful craps table** in the
browser — the product's centerpiece — rendering the Phase 1 event stream:
chips in their correct positions on the layout, dicer.io-style win/loss
fade-ups, point puck, dice, bankroll sparklines, a leaderboard of
realized-vs-theoretical edge, and roll distributions — plus full replay of
any recorded session.

## The Table (fidelity requirements — the heart of Phase 2)

The single-table view is validated **early**, before anything scales.
Fidelity, once proven, must survive scale-up — the beautiful table is the
anchor, not a later polish pass.

- **T1 — Faithful layout.** A real craps table rendition Mike is proud of:
  pass line & don't pass bar, come/don't come, the field, place/buy boxes
  4-5-6-8-9-10, and the center proposition area (hardways, hops, C&E, ATS).
  **No Big 6/8 — ever.** Reference image: `assets/Craps_table_layout.png`.
- **T2 — Correct chip placement.** Every `BetPlaced` event lands a chip in
  the right zone of the layout (place 6 chips sit on the 6 box, odds sit
  behind the line bet, come-bet chips travel to their number when the event
  stream moves them). A bet-type+number → felt-coordinate map is the core
  client-side artifact (per D3, coordinates never pollute engine events).
- **T3 — Win/loss fade-ups.** Resolutions animate dicer.io-style: a ghostly
  amount (+$14 / −$12) rises from the resolved bet's position and fades.
  Driven directly by `BetResolved` events.
- **T4 — Configurable table options, not fixed alternate layouts.** Real
  tables differ: field 2/12 double vs triple, ATS offered or not, hop bets,
  hardways, C&E availability. One parametric layout driven by a
  `TableOptions` config; named presets ("downtown", "strip", "bare-bones")
  are just saved configs. The felt renders only what the table offers, and
  the center section reflows to the enabled prop set. See D6.
- **T5 — Seating model is an open design decision:** many bots at one table
  (the engine already runs multi-player tables with shooter rotation) vs
  one bot per table. Decided in Step 3 planning with mockups, not before.

### D6 — Table options live in HouseRules (engine-enforced, default-open)

`HouseRules` already models field payouts (`field_bet_payout_2/12`); it
gains availability flags (`ats_enabled`, `hop_bets_enabled`,
`hardways_enabled`, `c_and_e_enabled`, ...). `Table.validate_bet` rejects
bets the table doesn't offer — an additive check whose defaults match
current behavior exactly, so every Phase 1 gate stays green. The UI then
renders precisely what the engine enforces: a strategy seated at a
bare-bones table that tries to bet ATS gets refused by the same rule the
felt displays. One source of truth, both directions.

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

Design references, in order of authority: **the T-requirements above** (the
faithful table beats everything), then `prototype/craps_observatory.jsx`
("The Rail") for the observatory chrome — pip-accurate dice, 120-point
bankroll sparklines with a dashed break-even line, the speed-control strip
1×/10×/100×/TURBO, and the leaderboard with max-drawdown and realized-edge
columns. The prototype's *mini felt cards* are a candidate for the zoomed-out
grid view only (a Step 3/T5 decision), never a substitute for the faithful
table. Its simplified
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
| ---- | ---- | ---- |
| 0 | Event JSON serialization + JSONL session recorder + `TableRunner`/`TableDirector` (no HTTP yet) | Recorded log replays to identical stats; Phase 1 gates green |
| 1 | FastAPI: create/configure table sessions (incl. `TableOptions`), SSE stream, pace/pause controls, replay + stats endpoints; D6 HouseRules flags + validate_bet enforcement | Two browsers watch one table in sync; reconnect resumes gaplessly; Phase 1 gates green with default options |
| 2 | **The Table.** Front end scaffold (Vite + React + TS + Tailwind) + the faithful single-table view: full layout (T1), bet-position map + correct chip placement (T2), win/loss fade-ups (T3), options-driven felt (T4), point puck, dice, sparkline | Mike is proud of it — explicit sign-off on the rendered table at 1× and TURBO before any scale work |
| 3 | Scale-up: seating-model decision (T5, with mockups), N-table/N-bot observatory, leaderboard (realized vs theoretical edge), roll distribution panel (per-table + aggregate) | Fidelity survives scale: the Step 2 table is unchanged in focus view; grid stays smooth at TURBO; leaderboard matches convergence numbers |
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

## Resolved questions

1. **Table configuration source** — JSON body on `POST /tables`, including
   `TableOptions` (D6/T4). *(Default accepted 2026-07-04.)*
2. **Scale target** — Phase 2 targets the prototype-scale grid (~6–12
   tables/bots); 100k-bot tournaments are Phase 3. *(Default accepted.)*
3. **Roll distributions** — both per-table and aggregate. *(Default
   accepted.)*

## Open questions for Mike

1. **T5 seating model** — many bots sharing one table vs one bot per table
   (or both, as a per-table choice). Decided at Step 3 planning, with
   mockups of each.
