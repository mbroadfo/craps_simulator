// @vitest-environment jsdom
import '@testing-library/jest-dom/vitest'
import { act, cleanup, render } from '@testing-library/react'
import { afterEach, beforeAll, beforeEach, describe, expect, it, vi } from 'vitest'
import { DiceAnimation } from './DiceAnimation'

// jsdom has no WebGL context, so the Three.js/Cannon-es scene inside
// DiceAnimation always falls back to its no-op path here (see its own
// try/catch around scene construction) — these tests exercise the
// phase-timing/onSettled/queueing contract App.tsx's gating depends
// on, which is deliberately decoupled from whether rendering works.
// Actual rendering quality can only be judged in a real browser.

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

describe('DiceAnimation phase timeline', () => {
  it('starts idle with no result', () => {
    const { container } = render(<DiceAnimation result={null} speed={1} onSettled={vi.fn()} />)
    expect(container.querySelector('.diceAnimation')).toHaveAttribute('data-phase', 'idle')
  })

  it('at normal speed: launches immediately, bounces at 700ms, settles and calls onSettled once at 1000ms', () => {
    const onSettled = vi.fn()
    const { container, rerender } = render(<DiceAnimation result={null} speed={1} onSettled={onSettled} />)
    rerender(<DiceAnimation result={[3, 4]} speed={1} onSettled={onSettled} />)

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
    const { container, rerender } = render(<DiceAnimation result={null} speed={10} onSettled={onSettled} />)
    rerender(<DiceAnimation result={[2, 5]} speed={10} onSettled={onSettled} />)

    expect(container.querySelector('.diceAnimation')).toHaveAttribute('data-phase', 'settled')
    expect(onSettled).toHaveBeenCalledTimes(1)
  })

  it('at 5x+ speed shortens the cycle to 300ms and skips the bounce phase entirely', () => {
    const onSettled = vi.fn()
    const { container, rerender } = render(<DiceAnimation result={null} speed={6} onSettled={onSettled} />)
    rerender(<DiceAnimation result={[1, 1]} speed={6} onSettled={onSettled} />)

    expect(container.querySelector('.diceAnimation')).toHaveAttribute('data-phase', 'launching')
    act(() => vi.advanceTimersByTime(300))
    expect(container.querySelector('.diceAnimation')).toHaveAttribute('data-phase', 'settled')
    expect(onSettled).toHaveBeenCalledTimes(1)
  })

  it('queues a new result that arrives mid-animation instead of restarting, then auto-chains the next cycle immediately', () => {
    const onSettled = vi.fn()
    const { container, rerender } = render(<DiceAnimation result={null} speed={1} onSettled={onSettled} />)
    rerender(<DiceAnimation result={[3, 3]} speed={1} onSettled={onSettled} />)

    act(() => vi.advanceTimersByTime(400)) // still mid-flight
    rerender(<DiceAnimation result={[5, 2]} speed={1} onSettled={onSettled} />)
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
})
