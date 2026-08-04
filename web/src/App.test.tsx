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
  start.mockResolvedValue(snapshot({ state: 'running' }))
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

    await act(async () => {
      fireEvent.click(screen.getByTitle('Roll — advance one roll, then stay paused'))
    })

    await waitFor(() => expect(step).toHaveBeenCalledWith('table-1'))
    // still paused, still enabled — no error, no crash
    expect(screen.getByTitle('Roll — advance one roll, then stay paused')).not.toBeDisabled()
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

// Regression test for a real reported bug: new bets (e.g. Come bets)
// placed by the engine between one roll's dice landing and the next
// roll's dice being thrown were invisible — accept_bets() (BetPlaced)
// always runs before roll_dice() for the *next* roll (see
// TableRunner.roll_once's own "accept -> roll -> resolve" docstring),
// so a BetPlaced arriving while the previous roll's animation was
// still in flight got swept into the same pendingEnvelopes queue as
// that roll's own resolution and only appeared in the instant
// everything flushed together — never as its own visible moment.
describe('App — BetPlaced is never held back by the dice-animation gate', () => {
  it('a BetPlaced that arrives mid-animation applies immediately, not only once the dice settle', async () => {
    await startTable()
    expect(onEnvelopeRef.current).not.toBeNull()

    // '$25' can legitimately appear elsewhere on screen (stats panel,
    // table limits, possibly more than once per chip depending on how
    // ChipStackLayer labels a single-chip stack) — count before/after
    // rather than assert an exact number, same spirit as
    // Felt.test.tsx's own chip-placement assertions.
    const before = screen.queryAllByText('$25').length

    await act(async () => {
      // A DiceRolled for the *previous* roll is still animating...
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

    // ...and nothing has settled it (no timer advanced, no onSettled
    // fired) when the engine's *next* roll_once() places a new Come
    // bet ahead of throwing those dice.
    await act(async () => {
      onEnvelopeRef.current?.({
        seq: 2,
        table_id: 'table-1',
        type: 'BetPlaced',
        player_name: 'Pass-Line',
        bet_type: 'Come',
        amount: 25,
        number: null,
      })
    })

    expect(screen.queryAllByText('$25').length).toBeGreaterThan(before)
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
})
