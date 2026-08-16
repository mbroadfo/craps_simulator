// @vitest-environment jsdom
import '@testing-library/jest-dom/vitest'
import { act, cleanup, render } from '@testing-library/react'
import { createRef } from 'react'
import { afterEach, beforeAll, beforeEach, describe, expect, it, vi } from 'vitest'
import { DiceAnimation, type DiceAnimationHandle } from './DiceAnimation'

// jsdom has no WebGL context, so the Three.js/Cannon-es scene inside
// DiceAnimation always falls back to its no-op path here (see its own
// try/catch around scene construction) — these tests exercise the
// phase-timing/onSettled/queueing contract App.tsx's gating depends
// on, which is deliberately decoupled from whether rendering works.
// Actual rendering quality can only be judged in a real browser.
//
// Rolls are pushed in via the imperative `enqueue()` handle, not a
// `result` prop — see the component's own docstring for why (a prop
// fed through setState can have several of its values collapse into
// one under React's batching, which is exactly the bug the "many
// enqueue() calls in one batch" tests below guard against).

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
  // jsdom has no audio decoding pipeline — HTMLMediaElement.play() rejects
  // with "not implemented" by default, which is exactly what the
  // component's own .catch(() => {}) is meant to swallow. Stub it so
  // that rejection doesn't spam the test output.
  window.HTMLMediaElement.prototype.play = () => Promise.resolve()
})

let felt: HTMLDivElement

beforeEach(() => {
  felt = document.createElement('div')
  felt.id = 'felt'
  felt.getBoundingClientRect = () =>
    ({ width: 1400, height: 851, top: 0, left: 0, right: 1400, bottom: 851, x: 0, y: 0, toJSON: () => {} }) as DOMRect
  document.body.appendChild(felt)
  vi.useFakeTimers()
})

afterEach(() => {
  cleanup()
  felt.remove()
  vi.useRealTimers()
})

function renderDice(speed: number, onSettled: () => void) {
  const ref = createRef<DiceAnimationHandle>()
  const view = render(<DiceAnimation ref={ref} speed={speed} onSettled={onSettled} />)
  return { ...view, ref }
}

describe('DiceAnimation phase timeline', () => {
  it('starts idle with nothing enqueued', () => {
    const { container } = renderDice(1, vi.fn())
    expect(container.querySelector('.diceAnimation')).toHaveAttribute('data-phase', 'idle')
  })

  it('at normal speed: launches immediately, bounces at 700ms, settles and calls onSettled once at 1000ms', () => {
    const onSettled = vi.fn()
    const { container, ref } = renderDice(1, onSettled)
    act(() => ref.current?.enqueue([3, 4]))

    expect(container.querySelector('.diceAnimation')).toHaveAttribute('data-phase', 'launching')

    act(() => vi.advanceTimersByTime(700))
    expect(container.querySelector('.diceAnimation')).toHaveAttribute('data-phase', 'bouncing')
    expect(onSettled).not.toHaveBeenCalled()

    act(() => vi.advanceTimersByTime(300))
    expect(container.querySelector('.diceAnimation')).toHaveAttribute('data-phase', 'settled')
    expect(onSettled).toHaveBeenCalledTimes(1)
  })

  it('at Turbo (speed >= 10) settles immediately with no visible flight', () => {
    const onSettled = vi.fn()
    const { container, ref } = renderDice(10, onSettled)
    act(() => ref.current?.enqueue([2, 5]))

    expect(container.querySelector('.diceAnimation')).toHaveAttribute('data-phase', 'settled')
    expect(onSettled).toHaveBeenCalledTimes(1)
  })

  it('at 5x and above the animation is fully skipped, same as Turbo — not just shortened', () => {
    const onSettled = vi.fn()
    const { container, ref } = renderDice(5, onSettled)
    act(() => ref.current?.enqueue([1, 1]))

    expect(container.querySelector('.diceAnimation')).toHaveAttribute('data-phase', 'settled')
    expect(onSettled).toHaveBeenCalledTimes(1)
  })

  it('just below the 5x threshold still plays the full animation', () => {
    const onSettled = vi.fn()
    const { container, ref } = renderDice(4.9, onSettled)
    act(() => ref.current?.enqueue([1, 1]))

    expect(container.querySelector('.diceAnimation')).toHaveAttribute('data-phase', 'launching')
    expect(onSettled).not.toHaveBeenCalled()
    act(() => vi.advanceTimersByTime(1000))
    expect(container.querySelector('.diceAnimation')).toHaveAttribute('data-phase', 'settled')
    expect(onSettled).toHaveBeenCalledTimes(1)
  })

  it('queues a new result that arrives mid-animation instead of restarting, then auto-chains the next cycle immediately', () => {
    const onSettled = vi.fn()
    const { container, ref } = renderDice(1, onSettled)
    act(() => ref.current?.enqueue([3, 3]))

    act(() => vi.advanceTimersByTime(400)) // still mid-flight
    act(() => ref.current?.enqueue([5, 2]))
    // the queued result must not restart the in-progress cycle
    expect(container.querySelector('.diceAnimation')).toHaveAttribute('data-phase', 'launching')
    expect(onSettled).not.toHaveBeenCalled()

    act(() => vi.advanceTimersByTime(600)) // first cycle settles at 1000ms total
    expect(onSettled).toHaveBeenCalledTimes(1)
    // second cycle (the queued [5,2]) starts immediately — no return-slide phase anymore
    expect(container.querySelector('.diceAnimation')).toHaveAttribute('data-phase', 'launching')

    act(() => vi.advanceTimersByTime(1000))
    expect(onSettled).toHaveBeenCalledTimes(2)
  })

  it('queues three overlapping results without losing any — onSettled fires once per result, in order', () => {
    // Regression test for a real reported bug: a single queued-result
    // slot let a third overlapping roll silently overwrite a second
    // one that had never gotten its own settle yet. App.tsx's per-
    // round envelope draining depends on onSettled() firing exactly
    // once per actual roll (see its own comment) — losing one meant
    // that round's bets/resolution never applied, and every later
    // round fell one settle further behind for the rest of the
    // session, eventually looking like the session had stalled.
    const onSettled = vi.fn()
    const { ref } = renderDice(1, onSettled)
    act(() => ref.current?.enqueue([3, 3]))

    // Two more rolls arrive back-to-back while the first is still
    // mid-flight — neither has settled yet.
    act(() => vi.advanceTimersByTime(200))
    act(() => ref.current?.enqueue([5, 2]))
    act(() => vi.advanceTimersByTime(200))
    act(() => ref.current?.enqueue([1, 6]))
    expect(onSettled).not.toHaveBeenCalled()

    // First cycle settles (started at t=0, 1000ms total) — only one
    // settle so far, and the second (not the third) cycle starts.
    act(() => vi.advanceTimersByTime(600))
    expect(onSettled).toHaveBeenCalledTimes(1)

    // Second cycle settles — the third one is still waiting, not lost.
    act(() => vi.advanceTimersByTime(1000))
    expect(onSettled).toHaveBeenCalledTimes(2)

    // Third cycle settles — nothing left queued.
    act(() => vi.advanceTimersByTime(1000))
    expect(onSettled).toHaveBeenCalledTimes(3)
  })

  it('never loses a roll when many enqueue() calls happen synchronously in the same batch (the actual reported bug)', () => {
    // Regression test for the real production incident: App.tsx used
    // to feed rolls in through a `result` prop driven by
    // setDiceResult(...), a plain React state setter. React batches
    // state updates — for a non-functional setState call, only the
    // *last* value in a batch survives. At Turbo (or just enough
    // backend-ahead-of-frontend backlog at any speed) many SSE
    // DiceRolled messages can be processed within a single JS tick,
    // before React ever renders — every setDiceResult call but the
    // last one was silently discarded, so DiceAnimation never even
    // saw most of the rolls, onSettled() fired far less than once per
    // round, and the felt looked like the session had stopped dozens
    // of shooters early even though the backend kept finishing
    // normally in the background. enqueue() is an imperative ref call,
    // outside React state entirely — every call here happens
    // synchronously inside one `act()`, simulating exactly that kind
    // of same-tick burst, and none may be lost.
    // Kept to 3 calls (1 running + 2 queued), under DEGRADE_QUEUE_DEPTH
    // — the separate "forces instant settling" test below covers what
    // happens once a backlog gets deep enough; this one stays focused
    // on proving the imperative-call-batching guarantee on its own,
    // with every roll still taking its own full normal-speed cycle.
    const onSettled = vi.fn()
    const { ref } = renderDice(1, onSettled)

    act(() => {
      ref.current?.enqueue([1, 1])
      ref.current?.enqueue([2, 2])
      ref.current?.enqueue([3, 3])
    })

    // Only the first has started animating; the other two are queued.
    expect(onSettled).not.toHaveBeenCalled()

    for (let expected = 1; expected <= 3; expected++) {
      act(() => vi.advanceTimersByTime(1000))
      expect(onSettled).toHaveBeenCalledTimes(expected)
    }
  })

  it('reset() drops any in-flight/queued cycle and returns to idle', () => {
    // A session reset (App.tsx's handleReset/attach) must clear this
    // component's own state too — it persists across sessions (no
    // remount) — or a stale mid-animation cycle from the *previous*
    // session could make a new session's first enqueue() queue behind
    // it instead of starting immediately.
    const onSettled = vi.fn()
    const { container, ref } = renderDice(1, onSettled)
    act(() => ref.current?.enqueue([3, 4]))
    act(() => ref.current?.enqueue([5, 2])) // queued, mid-flight

    act(() => ref.current?.reset())
    expect(container.querySelector('.diceAnimation')).toHaveAttribute('data-phase', 'idle')

    // Fully clocking out any timers the old cycle might have left
    // scheduled must not call onSettled — it was reset, not settled.
    act(() => vi.advanceTimersByTime(2000))
    expect(onSettled).not.toHaveBeenCalled()

    // A fresh enqueue() after reset starts a brand new cycle right away.
    act(() => ref.current?.enqueue([6, 6]))
    expect(container.querySelector('.diceAnimation')).toHaveAttribute('data-phase', 'launching')
    act(() => vi.advanceTimersByTime(1000))
    expect(onSettled).toHaveBeenCalledTimes(1)
  })

  it('picks up a mid-chain speed change for still-queued rolls, not just future ones', () => {
    // Regression test for a real reported bug: "moving the slider
    // while it's playing has no effect." At slow speeds the backend
    // routinely outpaces the ~1s animation, building a backlog in
    // queuedResults — settle() drains it by recursively calling
    // runCycle() from *within the same closure* the chain started
    // with. Reading the `speed` prop directly there meant every
    // queued roll kept animating at whatever speed was active when
    // the chain began, silently ignoring the slider for the rest of
    // a long backlog — sometimes the whole remainder of a session, if
    // the backend kept re-filling it as fast as the stale-speed
    // animation drained it. Reading speedRef.current instead picks up
    // the change on the very next queued roll.
    const onSettled = vi.fn()
    const { rerender, ref } = renderDice(1, onSettled)

    // Backlog of two: the first starts animating at 1x; the second
    // queues, since the first won't settle for another 1000ms.
    act(() => ref.current?.enqueue([3, 4]))
    act(() => ref.current?.enqueue([5, 2]))
    expect(onSettled).not.toHaveBeenCalled()

    // The slider moves to Turbo while the first roll is still mid-flight.
    rerender(<DiceAnimation ref={ref} speed={10} onSettled={onSettled} />)

    // First roll finishes out its original 1x cycle (already committed,
    // 1000ms later) — and the second (queued) roll must now animate at
    // the *new* speed, cascading to its own settle instantly rather
    // than taking another 1000ms, so both onSettled() calls land within
    // this same tick.
    act(() => vi.advanceTimersByTime(1000))
    expect(onSettled).toHaveBeenCalledTimes(2)
  })

  it('forces instant settling once the backlog is deep enough, then resumes normal speed once fully drained', () => {
    // At 1x the backend can outpace the ~1s animation even on a fast
    // machine (steady-state norm, not just a slow-PC symptom) — left
    // alone, the felt would drift further and further behind actual
    // game state for the rest of the session. Once queuedResults is
    // deep enough, subsequent rolls settle instantly (regardless of
    // the speed prop) until the backlog is fully drained, then normal-
    // speed animation resumes.
    const onSettled = vi.fn()
    const { ref } = renderDice(1, onSettled)

    act(() => {
      ref.current?.enqueue([1, 1]) // starts animating immediately at 1x (queue is empty)
      ref.current?.enqueue([2, 2]) // queues
      ref.current?.enqueue([3, 3]) // queues
      ref.current?.enqueue([4, 4]) // queues
      ref.current?.enqueue([5, 5]) // queues — 4 waiting once roll 1 settles, past the threshold
    })
    expect(onSettled).not.toHaveBeenCalled()

    // Roll 1 finishes its normal 1x cycle; by then the backlog is deep
    // enough that rolls 2-4 cascade through instantly in this same
    // tick, leaving only roll 5 — which finds an empty queue, clears
    // the degraded flag, and needs its own full cycle.
    act(() => vi.advanceTimersByTime(1000))
    expect(onSettled).toHaveBeenCalledTimes(4)

    act(() => vi.advanceTimersByTime(1000))
    expect(onSettled).toHaveBeenCalledTimes(5)
  })
})
