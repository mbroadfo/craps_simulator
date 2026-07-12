// @vitest-environment jsdom
// jest-dom's /vitest entry extends Vitest's own expect directly —
// the plain '@testing-library/jest-dom' import assumes Jest-style
// globals, which this project doesn't enable (see vite.config.ts —
// no `test.globals: true`).
import '@testing-library/jest-dom/vitest'
import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, beforeAll, describe, expect, it } from 'vitest'
import { Felt } from './Felt'

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
