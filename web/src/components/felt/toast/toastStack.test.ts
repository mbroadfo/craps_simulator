import { describe, expect, it } from 'vitest'
import type { Toast } from '../types'
import { stackedToastY } from './toastStack'

describe('stackedToastY', () => {
  it('places the first toast at its own target position, unmodified', () => {
    expect(stackedToastY([], 1080, 647)).toBe(647)
  })

  it('stacks a toast above an existing one anchored nearby (Pass Line vs Pass Line Odds), even though their raw targets already differ by less than STACK_OFFSET', () => {
    // Pass Line's toast already sits at 647; Pass Line Odds' own raw
    // target (684) is only 37px below it — less than STACK_OFFSET (46).
    // The result must clear the *existing* toast by a full STACK_OFFSET,
    // not just subtract 46 from the new toast's own (already-close) target.
    const existing: Toast[] = [{ id: 1, amount: 10, x: 1080, y: 647 }]
    const y = stackedToastY(existing, 1100, 684)
    expect(y).toBe(647 - 46)
    expect(Math.abs(y - 647)).toBeGreaterThanOrEqual(46)
  })

  it('does not stack toasts that are far apart on the felt', () => {
    const existing: Toast[] = [{ id: 1, amount: 10, x: 200, y: 200 }]
    expect(stackedToastY(existing, 1080, 647)).toBe(647)
  })

  it('keeps stacking a third toast above two already-nearby toasts', () => {
    const existing: Toast[] = [
      { id: 1, amount: 10, x: 1080, y: 647 },
      { id: 2, amount: -30, x: 1090, y: 601 },
    ]
    expect(stackedToastY(existing, 1085, 647)).toBe(601 - 46)
  })
})
