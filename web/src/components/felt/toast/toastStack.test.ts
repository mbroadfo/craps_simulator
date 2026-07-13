import { describe, expect, it } from 'vitest'
import type { Toast } from '../types'
import { stackedToastY } from './toastStack'

describe('stackedToastY', () => {
  it('places the first toast at its own target position, unmodified', () => {
    expect(stackedToastY([], 1080, 647)).toBe(647)
  })

  it('stacks a toast above an existing one anchored nearby (Pass Line vs Pass Line Odds)', () => {
    const existing: Toast[] = [{ id: 1, amount: 10, x: 1080, y: 647 }]
    expect(stackedToastY(existing, 1100, 684)).toBe(684 - 46)
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
    expect(stackedToastY(existing, 1085, 647)).toBe(647 - 2 * 46)
  })
})
