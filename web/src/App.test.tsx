// @vitest-environment jsdom
import '@testing-library/jest-dom/vitest'
import { act, cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeAll, beforeEach, describe, expect, it, vi } from 'vitest'
import App from './App'
import type { TableSnapshot } from './lib/api'

// The whole SSE module is mocked out. Most tests below only care about
// the REST-driven pause/resume/step/speed handlers, but the envelope
// gating regression test needs to fire synthetic stream events, so the
// mock captures whatever callback attach() actually registered.
const { onEnvelopeRef } = vi.hoisted(() => ({
  onEnvelopeRef: { current: null as ((e: unknown) => void) | null },
}))
vi.mock('./lib/sse', () => ({
  connectTableStream: vi.fn((_tableId: string, onEnvelope: (e: unknown) => void) => {
    onEnvelopeRef.current = onEnvelope
    return { close: vi.fn() }
  }),
}))

const listStrategies = vi.fn()
const createTable = vi.fn()
const start = vi.fn()
const pause = vi.fn()
const resume = vi.fn()
const step = vi.fn()
const setPace = vi.fn()

vi.mock('./lib/api', () => ({
  api: {
    listStrategies: (...args: unknown[]) => listStrategies(...args),
    createTable: (...args: unknown[]) => createTable(...args),
    start: (...args: unknown[]) => start(...args),
    pause: (...args: unknown[]) => pause(...args),
    resume: (...args: unknown[]) => resume(...args),
    step: (...args: unknown[]) => step(...args),
    setPace: (...args: unknown[]) => setPace(...args),
    stop: vi.fn(),
  },
}))

// LiveFelt's dice animation needs the same environment stubs
// Felt.test.tsx/DiceAnimation.test.tsx use, and SessionGraph's
// recharts <ResponsiveContainer> needs a ResizeObserver to exist at
// all (jsdom has neither).
beforeAll(() => {
  if (!('ResizeObserver' in globalThis)) {
    class ResizeObserverStub {
      observe() {}
      unobserve() {}
      disconnect() {}
    }
    // @ts-expect-error -- test-only stub, not a full ResizeObserver
    globalThis.ResizeObserver = ResizeObserverStub
  }
  window.HTMLMediaElement.prototype.play = () => Promise.resolve()
})

afterEach(() => {
  cleanup()
  vi.clearAllMocks()
})

function snapshot(overrides: Partial<TableSnapshot> = {}): TableSnapshot {
  return {
    table_id: 'table-1',
    state: 'paused',
    roll_delay_ms: 500,
    next_seq: 0,
    session_rolls: 0,
    shooter_index: 0,
    puck_on: false,
    point: null,
    players: [{ name: 'Pass-Line', strategy: 'Pass-Line', bankroll: 1000 }],
    recording: null,
    ...overrides,
  }
}

// Drives the app through the same path a real user does: wait for the
// lineup to load, click Start, wait for the rail to flip into its
// "table exists" state (Start becomes Roll) — everything downstream
// reuses this instead of poking at App's internals directly, since
// handlePauseResume/handleStep/handleSpeedChange are closures with no
// exported seam of their own.
async function startTable() {
  listStrategies.mockResolvedValue([
    { name: 'Pass-Line', dealer_call: '$10 on the line' },
    { name: 'Iron Cross', dealer_call: '$10 on the line — inside for $34 and the field' },
    { name: '3-Point Molly', dealer_call: "$10 on the line, chasing two come bets with odds" },
  ])
  createTable.mockResolvedValue(snapshot({ state: 'created' }))
  // handleStart calls start(id, true) directly — the table lands
  // paused without a separate pause() round trip (see App.tsx's
  // handleStart comment on why the old start()-then-pause() lost the
  // race against table_session.py's drive loop almost every time).
  start.mockResolvedValue(snapshot({ state: 'paused' }))
  pause.mockResolvedValue(snapshot({ state: 'paused' }))

  render(<App />)
  const startBtn = await screen.findByTitle('Start')
  await waitFor(() => expect(startBtn).not.toBeDisabled())

  await act(async () => {
    fireEvent.click(startBtn)
  })
  await waitFor(() => expect(screen.getByTitle('Roll — advance one roll, then stay paused')).toBeInTheDocument())
}

// These three race against the SSE stream (see App.tsx's own comment
// on handlePauseResume/handleStep/handleSpeedChange): the server can
// legitimately 409 a request that was valid when the button was
// clicked. The regression this guards is a real bug — that rejection
// used to be unhandled and crashed the dev overlay (see the "409 on
// /pause" incident this fix was written for) — so every test here
// checks both that a rejection surfaces as a visible error (not a
// crash) and that a normal success still updates the rail as before.
describe('App — pause/resume/step/speed error handling', () => {
  it('handlePauseResume: a rejected request surfaces as an error message, not an unhandled rejection', async () => {
    await startTable()
    resume.mockRejectedValueOnce(new Error('409: table finished'))

    await act(async () => {
      fireEvent.click(screen.getByTitle('Autoplay — roll continuously'))
    })

    expect(await screen.findByText(/409: table finished/)).toBeInTheDocument()
  })

  it('handlePauseResume: a successful call updates the rail to reflect the new state', async () => {
    await startTable()
    resume.mockResolvedValueOnce(snapshot({ state: 'running' }))

    await act(async () => {
      fireEvent.click(screen.getByTitle('Autoplay — roll continuously'))
    })

    expect(await screen.findByTitle('Pause — stop auto-rolling')).toBeInTheDocument()
  })

  it('handleStep: a rejected request surfaces as an error message, not an unhandled rejection', async () => {
    await startTable()
    step.mockRejectedValueOnce(new Error('409: table finished'))

    await act(async () => {
      fireEvent.click(screen.getByTitle('Roll — advance one roll, then stay paused'))
    })

    expect(await screen.findByText(/409: table finished/)).toBeInTheDocument()
  })

  it('handleStep: a successful call updates the snapshot from the response', async () => {
    await startTable()
    step.mockResolvedValueOnce(snapshot({ state: 'paused', session_rolls: 1 }))
    const rollBtn = () => screen.getByTitle('Roll — advance one roll, then stay paused')

    await act(async () => {
      fireEvent.click(rollBtn())
    })

    await waitFor(() => expect(step).toHaveBeenCalledWith('table-1'))
    // No error, no crash — but still disabled: a successful REST
    // response alone doesn't re-enable Roll, only the next round's
    // RoundReady event (over SSE) does, once its bets are revealed —
    // see App.tsx's two-phase reveal state machine.
    expect(rollBtn()).toBeDisabled()

    await act(async () => {
      onEnvelopeRef.current?.({ seq: 1, table_id: 'table-1', type: 'RoundReady', bet_count: 0 })
    })
    expect(rollBtn()).not.toBeDisabled()
  })

  it('handleSpeedChange: a rejected request surfaces as an error message, not an unhandled rejection', async () => {
    await startTable()
    setPace.mockRejectedValueOnce(new Error('409: table finished'))

    await act(async () => {
      fireEvent.click(screen.getByTitle('Turbo — jump to max speed'))
    })

    expect(await screen.findByText(/409: table finished/)).toBeInTheDocument()
  })

  it('handleSpeedChange: a successful call reaches the API with the expected roll delay', async () => {
    await startTable()
    setPace.mockResolvedValueOnce(snapshot({ state: 'paused', roll_delay_ms: 0 }))

    await act(async () => {
      fireEvent.click(screen.getByTitle('Turbo — jump to max speed'))
    })

    await waitFor(() => expect(setPace).toHaveBeenCalledWith('table-1', 0)) // Turbo = 0ms delay
  })
})

// Regression test for the two-phase roll cycle: table_session.py's
// _drive() now publishes a round's bets (BetsRequested, BetPlaced,
// RoundReady) strictly *before* that round's own DiceRolled — the
// opposite order from the old atomic roll_once(). BetPlaced used to be
// exempt from every gate (it always belonged to the *next* roll under
// the old cadence); now the *next* round's prep must be held back
// until the *current* round's animation settles AND an extra
// REVEAL_DELAY_MS has passed, so the just-resolved round's toasts get
// a moment on screen before new chips land on top of them.
describe('App — next round\'s bets wait for this round\'s animation and reveal delay', () => {
  beforeEach(() => {
    vi.useFakeTimers({ shouldAdvanceTime: true })
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('holds a new round\'s BetPlaced/RoundReady back until the current animation settles, then the extra reveal delay', async () => {
    await startTable()
    expect(onEnvelopeRef.current).not.toBeNull()

    const before = screen.queryAllByText('$25').length
    const rollBtn = () => screen.getByTitle('Roll — advance one roll, then stay paused')

    // Round N's dice are thrown (not settled yet)...
    await act(async () => {
      onEnvelopeRef.current?.({
        seq: 1,
        table_id: 'table-1',
        type: 'DiceRolled',
        shooter_index: 0,
        roll_number: 1,
        dice: [3, 4],
        total: 7,
        phase: 'point',
        point: 6,
        table_risk: 0,
        shooter_name: 'Pass-Line',
      })
    })
    expect(rollBtn()).toBeDisabled()

    // ...and round N+1's bets are already published, per
    // table_session.py's _drive(): prepare_next_roll() runs ungated,
    // strictly before the pause gate/pace ever let roll_and_resolve()
    // fire for round N+1.
    await act(async () => {
      onEnvelopeRef.current?.({ seq: 2, table_id: 'table-1', type: 'BetsRequested' })
      onEnvelopeRef.current?.({
        seq: 3,
        table_id: 'table-1',
        type: 'BetPlaced',
        player_name: 'Pass-Line',
        bet_type: 'Come',
        amount: 25,
        number: null,
      })
      onEnvelopeRef.current?.({ seq: 4, table_id: 'table-1', type: 'RoundReady', bet_count: 1 })
    })

    // Not visible yet — round N hasn't even settled.
    expect(screen.queryAllByText('$25').length).toBe(before)
    expect(rollBtn()).toBeDisabled()

    // Round N's dice animation settles (1000ms at default 1x speed).
    await act(async () => vi.advanceTimersByTime(1000))

    // Still not visible — that only flushed round N's own queue;
    // round N+1's reveal is on its own, later timer.
    expect(screen.queryAllByText('$25').length).toBe(before)
    expect(rollBtn()).toBeDisabled()

    // The extra reveal delay passes.
    await act(async () => vi.advanceTimersByTime(500))

    expect(screen.queryAllByText('$25').length).toBeGreaterThan(before)
    expect(rollBtn()).not.toBeDisabled()
  })

  it('reveals immediately (no held-back queue) for the very first round after Start, before any roll has happened', async () => {
    await startTable()

    const before = screen.queryAllByText('$25').length

    await act(async () => {
      onEnvelopeRef.current?.({ seq: 1, table_id: 'table-1', type: 'BetsRequested' })
      onEnvelopeRef.current?.({
        seq: 2,
        table_id: 'table-1',
        type: 'BetPlaced',
        player_name: 'Pass-Line',
        bet_type: 'Pass Line',
        amount: 25,
        number: null,
      })
      onEnvelopeRef.current?.({ seq: 3, table_id: 'table-1', type: 'RoundReady', bet_count: 1 })
    })

    expect(screen.queryAllByText('$25').length).toBeGreaterThan(before)
    expect(screen.getByTitle('Roll — advance one roll, then stay paused')).not.toBeDisabled()
  })

  it('never doubles a Pass Line chip into $20 when the backend outpaces the dice animation (regression for a real reported bug)', async () => {
    // At the default pace (500ms between rolls) the backend routinely
    // gets ahead of the ~1000ms dice-settle animation: a second
    // round's entire prep-and-resolution can arrive before the first
    // round's own dice have even landed. flushOneRoundOfPending/
    // flushOneRoundOfReveal (App.tsx) must drain exactly one round at
    // a time regardless — flushing everything queued used to apply a
    // later round's resolution before its own BetPlaced had even been
    // revealed, orphaning the pop and letting the *next* round's
    // BetPlaced stack onto the same felt zone once the reveal queue
    // caught up: two separate $10 Pass Line placements merging into
    // one $20 pile.
    await startTable()
    const twentyDollarChips = () => screen.queryAllByText('$20').length

    await act(async () => {
      onEnvelopeRef.current?.({
        seq: 1, table_id: 'table-1', type: 'DiceRolled',
        shooter_index: 0, roll_number: 1, dice: [3, 4], total: 7,
        phase: 'come-out', point: null, table_risk: 0, shooter_name: 'Pass-Line',
      })
      onEnvelopeRef.current?.({
        seq: 2, table_id: 'table-1', type: 'BetResolved',
        player_name: 'Pass-Line', bet_type: 'Pass Line', amount: 10, number: null,
        status: 'won', payout: 20, win_payout: 20, removed: true,
      })
      // Round 2's full prep-and-resolution, and round 3's prep, all
      // arrive before round 1's animation has settled at all.
      onEnvelopeRef.current?.({ seq: 3, table_id: 'table-1', type: 'BetsRequested' })
      onEnvelopeRef.current?.({
        seq: 4, table_id: 'table-1', type: 'BetPlaced',
        player_name: 'Pass-Line', bet_type: 'Pass Line', amount: 10, number: null,
      })
      onEnvelopeRef.current?.({ seq: 5, table_id: 'table-1', type: 'RoundReady', bet_count: 1 })
      onEnvelopeRef.current?.({
        seq: 6, table_id: 'table-1', type: 'DiceRolled',
        shooter_index: 0, roll_number: 2, dice: [2, 5], total: 7,
        phase: 'come-out', point: null, table_risk: 0, shooter_name: 'Pass-Line',
      })
      onEnvelopeRef.current?.({
        seq: 7, table_id: 'table-1', type: 'BetResolved',
        player_name: 'Pass-Line', bet_type: 'Pass Line', amount: 10, number: null,
        status: 'won', payout: 20, win_payout: 20, removed: true,
      })
      onEnvelopeRef.current?.({ seq: 8, table_id: 'table-1', type: 'BetsRequested' })
      onEnvelopeRef.current?.({
        seq: 9, table_id: 'table-1', type: 'BetPlaced',
        player_name: 'Pass-Line', bet_type: 'Pass Line', amount: 10, number: null,
      })
      onEnvelopeRef.current?.({ seq: 10, table_id: 'table-1', type: 'RoundReady', bet_count: 1 })
    })
    expect(twentyDollarChips()).toBe(0)

    // Round 1's animation settles — only round 1's own resolution applies.
    await act(async () => vi.advanceTimersByTime(1000))
    expect(twentyDollarChips()).toBe(0)

    // Round 2's reveal delay passes — its lone $10 Pass Line appears.
    await act(async () => vi.advanceTimersByTime(500))
    expect(twentyDollarChips()).toBe(0)

    // Round 2's own (chained) animation settles, popping that chip...
    await act(async () => vi.advanceTimersByTime(1000))
    expect(twentyDollarChips()).toBe(0)

    // ...and round 3's reveal delay passes — its own lone $10 Pass
    // Line appears. Never stacked with a leftover from round 2.
    await act(async () => vi.advanceTimersByTime(500))
    expect(twentyDollarChips()).toBe(0)
  })
})

describe('App — Roll button re-enable gating', () => {
  it('clicking Roll disables it immediately, optimistically, before any envelope arrives', async () => {
    step.mockResolvedValue(snapshot({ state: 'paused' }))
    await startTable()
    const rollBtn = screen.getByTitle('Roll — advance one roll, then stay paused')
    expect(rollBtn).not.toBeDisabled()

    await act(async () => {
      fireEvent.click(rollBtn)
    })

    expect(rollBtn).toBeDisabled()
  })

  it('a rejected step() call re-enables the button', async () => {
    step.mockRejectedValueOnce(new Error('409: table finished'))
    await startTable()
    const rollBtn = screen.getByTitle('Roll — advance one roll, then stay paused')

    await act(async () => {
      fireEvent.click(rollBtn)
    })

    await waitFor(() => expect(rollBtn).not.toBeDisabled())
  })
})

// Dealer-call speech bubble (Observatory panel roster, Tier 1): fires
// immediately on ShooterAssigned (not gated behind the dice-animation
// queue — see App.tsx's own comment on why) and auto-hides after 3s,
// owned entirely by App.tsx's timer (DealerCallBubble itself has none
// — see its header comment).
describe('App — dealer-call speech bubble', () => {
  beforeEach(() => {
    // shouldAdvanceTime lets real time keep ticking (so startTable()'s
    // internal waitFor polling still works) while still allowing an
    // explicit vi.advanceTimersByTime() jump for the 3s auto-hide.
    vi.useFakeTimers({ shouldAdvanceTime: true })
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('shows the matching shooter\'s dealer call on ShooterAssigned, then hides it after 3s', async () => {
    await startTable()
    expect(onEnvelopeRef.current).not.toBeNull()

    await act(async () => {
      onEnvelopeRef.current?.({
        seq: 1,
        table_id: 'table-1',
        type: 'ShooterAssigned',
        shooter_index: 0,
        shooter_name: 'Pass-Line',
      })
    })

    expect(screen.getByText('$10 on the line')).toBeInTheDocument()

    await act(async () => vi.advanceTimersByTime(3000))

    expect(screen.queryByText('$10 on the line')).not.toBeInTheDocument()
  })

  it('re-announces the same shooter\'s call on PointHit (they keep the dice and start a fresh come-out)', async () => {
    await startTable()

    await act(async () => {
      onEnvelopeRef.current?.({
        seq: 1,
        table_id: 'table-1',
        type: 'ShooterAssigned',
        shooter_index: 0,
        shooter_name: 'Pass-Line',
      })
    })
    expect(screen.getByText('$10 on the line')).toBeInTheDocument()

    // bubble auto-hides...
    await act(async () => vi.advanceTimersByTime(3000))
    expect(screen.queryByText('$10 on the line')).not.toBeInTheDocument()

    // ...then the shooter makes their point and keeps the dice — a
    // fresh come-out for the *same* shooter re-announces the call,
    // even though no new ShooterAssigned fired.
    await act(async () => {
      onEnvelopeRef.current?.({ seq: 2, table_id: 'table-1', type: 'PointHit', point: 6 })
    })
    expect(screen.getByText('$10 on the line')).toBeInTheDocument()
  })

  it('PointHit before any shooter is assigned does nothing (no crash, no stray bubble)', async () => {
    await startTable()

    await act(async () => {
      onEnvelopeRef.current?.({ seq: 1, table_id: 'table-1', type: 'PointHit', point: 6 })
    })

    expect(screen.queryByText('$10 on the line')).not.toBeInTheDocument()
  })
})
