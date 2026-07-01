# Phase 1 Brief — Event-Sourced Core & Pure Strategy Contract

**Owner:** Mike Broadfoot (architect / decision maker)
**Goal:** Break the complexity wall that stalled this codebase by decoupling
strategies, statistics, logging, and the API from the engine — without changing
one cent of payout math.

## Vision (context, not scope)

A craps observatory: one or many tables rendered live, bots running different
strategies, roll distributions and realized-vs-theoretical edge per strategy,
and eventually an AI Strategy Lab where LLM-generated strategies compete in
100k-session tournaments. None of that is Phase 1 — but Phase 1 makes it
possible. The UI prototype lives in `prototype/` as the north star.

## Current-state findings (verified against this repo)

- **God object:** `CrapsEngine` ([craps/craps_engine.py](craps/craps_engine.py))
  holds 12+ `Optional` components (`table`, `dice`, `stats`, `play_by_play`,
  `rules_engine`, `player_lineup`, ...) wired together in `setup_session`.
  Every method begins with a null-check litany.
- **Strategy coupling:** strategies subclass `BaseStrategy`
  ([craps/base_strategy.py](craps/base_strategy.py)) with 8 methods/hooks
  (`place_bets`, `adjust_bets`, `remove_bets`, `turn_off_bets`,
  `turn_on_bets`, `on_new_shooter`, `notify_payout`, `notify_roll`,
  `reset_shooter_state`). They receive the live `Table` and mutate it;
  `PassLineStrategy` even takes `table` in its **constructor**
  ([craps/strategies/pass_line_strategy.py:19](craps/strategies/pass_line_strategy.py#L19))
  and manufactures bets via `table.rules_engine.create_bet(...)`.
- **Non-deterministic dice:** `Dice.roll()` uses the global `random` module
  ([craps/dice.py:67](craps/dice.py#L67)) — no seed parameter. It *does*
  support `forced_rolls` (deque) and CSV roll-history replay; that is the
  determinism mechanism the regression harness will build on.
- **Side-effect soup:** `resolve_bets` interleaves ATS tracking, bet
  settlement, stats updates, strategy notification, state transition, and
  strategy adjustment in one method
  ([craps/craps_engine.py:217](craps/craps_engine.py#L217)).
- **Global config:** players come from the `ACTIVE_PLAYERS` dict in
  [config.py](config.py); `simulate_single_session()` takes no arguments, so
  parallel sessions can't vary strategy, seed, or bankroll.
- **The keep:** `RulesEngine` payout/bet-validity logic and the 16-strategy
  library are the hard-won assets. Preserve behavior exactly.

## Target architecture

1. **Event-sourced core.** The engine emits typed roll events
   (`BetsPlaced`, `DiceRolled`, `BetResolved`, `PointEstablished`,
   `SevenOut`, `ShooterChanged`, ...). Statistics, play-by-play logging,
   roll history, and the API become **consumers** of the event stream.
   The engine never calls them directly.
2. **Pure strategy contract v2.** A strategy is
   `wants(state: TableView) -> Layout` — given an immutable snapshot
   (phase, point, own bets, bankroll, roll history tail, house rules),
   return the layout of bets you want plus an opaque `memo` for state the
   strategy carries between rolls. The engine diffs desired vs. current
   layout, funds the delta, and resolves. No `Table` mutation, no
   `rules_engine` access, no constructor dependencies. This is the contract
   an LLM can reliably generate against (Phase 4).
3. **Deterministic sessions.** `Dice` accepts an injected
   `random.Random(seed)`; `simulate_single_session(seed, lineup, rules)`
   is fully parameterized. Same seed → identical event stream → identical
   bankrolls, forever.

## Non-negotiable constraints

- **Zero payout drift.** `RulesEngine` payout tables and bet-validity rules
  are read-only this phase.
- **Regression harness is the gate.** Old engine and new engine, fed
  identical dice (forced-roll lists / CSV replay), must produce identical
  per-roll bankrolls for every player. A PR that can't prove this doesn't merge.
- **`run_simulation.py` CLI keeps working unchanged** through the whole phase.
- **Quality bar:** mypy clean, pytest green, small commits.

## PR breakdown

| PR | Scope | Merge gate |
|----|-------|-----------|
| 1 | Event types + event bus; engine emits events alongside existing behavior (parallel-run, nothing consumes yet) | Existing tests green; events fire for every roll |
| 2 | Strategy contract v2 (`wants(state)`), engine-side layout diff/funding; port `PassLineStrategy` + `IronCrossStrategy`; seeded-RNG regression harness | Harness proves identical bankrolls old-vs-new for both strategies over ≥10k forced rolls |
| 3 | Port remaining 14 strategies to v2 | Harness passes for every strategy |
| 4 | Convert `statistics`, `play_by_play`, roll history, FastAPI layer to event consumers; delete direct calls | `run_simulation.py` output unchanged; house-edge convergence test (1M rolls: pass line −1.41% ±0.15, field −2.78% ±0.2, place 6/8 −1.52% ±0.15) |

## Working agreement

Plan mode first, always. Propose the plan for one PR at a time; Mike reviews
and annotates before any code is written. Small commits with meaningful
messages. When behavior questions arise, the old engine's observed behavior
is the spec — even where it looks wrong, flag it, don't fix it silently.
