// @vitest-environment jsdom
// jest-dom's /vitest entry extends Vitest's own expect directly —
// the plain '@testing-library/jest-dom' import assumes Jest-style
// globals, which this project doesn't enable (see vite.config.ts —
// no `test.globals: true`).
import '@testing-library/jest-dom/vitest'
import { act, cleanup, fireEvent, render, screen } from '@testing-library/react'
import { createRef } from 'react'
import { afterEach, beforeAll, beforeEach, describe, expect, it, vi } from 'vitest'
import type { DiceAnimationHandle } from './dice/DiceAnimation'
import { Felt, LiveFelt } from './Felt'
import { initialRollLogState } from './state/liveRollLog'
import { initialState } from '../../lib/tableReducer'

// jsdom doesn't implement ResizeObserver (used by useSidebarAutoFit) —
// a plain stub is the standard fix, same as any other component that
// measures layout via ResizeObserver.
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
  // jsdom has no audio decoding pipeline — HTMLMediaElement.play()
  // rejects with "not implemented" by default; LiveFelt's dice
  // animation plays a roll sound, so this needs the same stub
  // DiceAnimation.test.tsx uses. pause() is stubbed too since the
  // animation now cuts the clip short at settle time.
  window.HTMLMediaElement.prototype.play = () => Promise.resolve()
  window.HTMLMediaElement.prototype.pause = () => {}
})

// RTL's auto-cleanup-between-tests relies on detecting a global
// `afterEach` hook; this project doesn't set `test.globals: true` (see
// vite.config.ts), so it never registers on its own — without this,
// every render() in this file piles up in the same document instead
// of unmounting, and testid/text queries start finding duplicates.
afterEach(() => {
  cleanup()
})

describe('Felt', () => {
  it('renders every major landmark without throwing', () => {
    render(<Felt />)

    for (const n of [4, 5, 6, 8, 9, 10]) {
      expect(screen.getByTestId(`box-${n}`)).toBeInTheDocument()
    }
    expect(screen.getByText('Six')).toBeInTheDocument()
    expect(screen.getByText('Nine')).toBeInTheDocument()

    expect(screen.getByTestId('dont-come')).toBeInTheDocument()
    expect(screen.getByText("Don't")).toBeInTheDocument()
    expect(screen.getAllByText('Come').length).toBeGreaterThan(0)

    // Pass Line / Don't Pass band text renders twice each (bottom
    // strip + rotated right-rail copy).
    expect(screen.getAllByText('Pass Line').length).toBeGreaterThan(0)
    expect(screen.getAllByText("Don't Pass").length).toBeGreaterThan(0)

    expect(screen.getByTestId('chip-rail')).toBeInTheDocument()

    for (const title of ['Table Limits', 'Current', 'Session', 'Distribution', 'Efficiency', 'Strategy']) {
      expect(screen.getByTestId(`stats-section-${title}`)).toBeInTheDocument()
    }
  })

  it('click-to-place still places a chip after the imperative-to-declarative rewrite', () => {
    render(<Felt />)

    // $25 already renders once, in the denom picker's own chip face —
    // count rather than assert presence/absence outright.
    const before = screen.getAllByText('$25').length
    fireEvent.click(screen.getByTestId('place-4'))
    const after = screen.getAllByText('$25').length

    expect(after).toBe(before + 1)
  })

  it('right-click removes the chip it just placed', () => {
    render(<Felt />)

    fireEvent.click(screen.getByTestId('place-5'))
    const withChip = screen.getAllByText('$25').length

    fireEvent.contextMenu(screen.getByTestId('place-5'))
    const afterRemove = screen.getAllByText('$25').length

    expect(afterRemove).toBe(withChip - 1)
  })
})

// Thin prop-plumbing checks — DiceAnimation's own phase/timing/queueing
// behavior is fully covered by dice/DiceAnimation.test.tsx; these only
// confirm LiveFelt actually threads the diceAnimationRef/diceSpeed/
// onDiceSettled through to it rather than dropping them.
describe('LiveFelt dice wiring', () => {
  const noop = () => {}

  function renderLive(diceSpeed: number, onDiceSettled: () => void) {
    const diceAnimationRef = createRef<DiceAnimationHandle>()
    const view = render(
      <LiveFelt
        tableState={initialState()}
        rollLog={initialRollLogState()}
        playerName=""
        setPlayerName={noop}
        roster={[]}
        setTableState={noop}
        diceAnimationRef={diceAnimationRef}
        diceSpeed={diceSpeed}
        onDiceSettled={onDiceSettled}
      />,
    )
    return { ...view, diceAnimationRef }
  }

  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('starts idle with nothing enqueued', () => {
    const { container } = renderLive(1, noop)
    expect(container.querySelector('.diceAnimation')).toHaveAttribute('data-phase', 'idle')
  })

  it('forwards the ref through so App.tsx can enqueue a roll and start the animation', () => {
    const { container, diceAnimationRef } = renderLive(1, noop)
    act(() => diceAnimationRef.current?.enqueue([3, 4]))
    expect(container.querySelector('.diceAnimation')).toHaveAttribute('data-phase', 'launching')
  })

  it('wires onDiceSettled through end-to-end — it fires once the animation settles', () => {
    const onDiceSettled = vi.fn()
    const { diceAnimationRef } = renderLive(1, onDiceSettled)
    act(() => diceAnimationRef.current?.enqueue([3, 4]))

    act(() => vi.advanceTimersByTime(1000)) // normal-speed cycle: 700ms flight + 300ms bounce
    expect(onDiceSettled).toHaveBeenCalledTimes(1)
  })
})

// A bet toggled "inactive" (Place/Buy/Lay off during come-out,
// Come/Don't Come Odds off unless called on) must render dimmed
// instead of full-opacity, so a viewer can tell an "off" pile apart
// from a working one at a glance.
describe('LiveFelt chip status rendering', () => {
  const noop = () => {}

  function renderWithChip(status: string) {
    const tableState = initialState()
    tableState.chips.set('k1', {
      player: 'Molly',
      betType: 'Place',
      number: 6,
      amounts: [30],
      status,
    })
    return render(
      <LiveFelt
        tableState={tableState}
        rollLog={initialRollLogState()}
        playerName="Molly"
        setPlayerName={noop}
        roster={[]}
        setTableState={noop}
        diceAnimationRef={createRef<DiceAnimationHandle>()}
        diceSpeed={1}
        onDiceSettled={noop}
      />,
    )
  }

  it('dims an inactive chip stack', () => {
    const { container } = renderWithChip('inactive')
    const group = container.querySelector('[data-testid="chip-stack-layer"] > g')
    expect(group).toHaveAttribute('opacity', '0.45')
  })

  it('renders an active chip stack at full opacity', () => {
    const { container } = renderWithChip('active')
    const group = container.querySelector('[data-testid="chip-stack-layer"] > g')
    expect(group).toHaveAttribute('opacity', '1')
  })
})
