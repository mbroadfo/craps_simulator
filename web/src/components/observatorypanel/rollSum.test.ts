import { describe, expect, it } from 'vitest'
import { formatRollSum } from './rollSum'

describe('formatRollSum', () => {
  it('shows an em dash before any roll', () => {
    expect(formatRollSum(null)).toBe('—')
  })

  it('shows a plain sum for a non-matching roll', () => {
    expect(formatRollSum([3, 4])).toBe('7')
  })

  it('marks 4/6/8/10 made as a matching pair as hardways', () => {
    expect(formatRollSum([2, 2])).toBe('4H')
    expect(formatRollSum([3, 3])).toBe('6H')
    expect(formatRollSum([4, 4])).toBe('8H')
    expect(formatRollSum([5, 5])).toBe('10H')
  })

  it('does not mark 2 or 12 as hardways even though they are matching pairs', () => {
    expect(formatRollSum([1, 1])).toBe('2')
    expect(formatRollSum([6, 6])).toBe('12')
  })
})
