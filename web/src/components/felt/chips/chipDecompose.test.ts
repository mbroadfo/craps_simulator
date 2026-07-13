import { describe, expect, it } from 'vitest'
import { chipDenomsForAmount, rackDenomsForAmount } from './chipDecompose'

const sum = (denoms: number[]) => denoms.reduce((s, d) => s + d, 0)

describe('chipDenomsForAmount', () => {
  it('greedily breaks an odds-bet amount into real denominations', () => {
    expect(chipDenomsForAmount(37)).toEqual([25, 5, 5, 1, 1])
  })

  it('breaks a small place-bet amount', () => {
    expect(chipDenomsForAmount(6)).toEqual([5, 1])
  })

  it('always sums back to the original amount, across a range of bet sizes', () => {
    for (const amount of [1, 5, 6, 10, 25, 37, 100, 110, 250, 1100, 3700]) {
      expect(sum(chipDenomsForAmount(amount))).toBe(amount)
    }
  })

  it('rounds a fractional amount to the nearest dollar before decomposing', () => {
    expect(sum(chipDenomsForAmount(37.4))).toBe(37)
  })

  it('returns an empty stack for zero', () => {
    expect(chipDenomsForAmount(0)).toEqual([])
  })
})

describe('rackDenomsForAmount', () => {
  it('prefers small denominations for texture instead of one dominant chip', () => {
    const denoms = rackDenomsForAmount(530)
    expect(sum(denoms)).toBe(530)
    // The whole point: a $500 bankroll should not collapse to
    // essentially one chip — plenty of $5/$25 should still show up.
    expect(denoms.filter((d) => d === 5).length).toBeGreaterThan(0)
    expect(denoms.filter((d) => d === 25).length).toBeGreaterThan(0)
  })

  it('makes a modest bet-sized amount visibly textured (many small chips)', () => {
    const denoms = rackDenomsForAmount(37)
    expect(sum(denoms)).toBe(37)
    expect(denoms.length).toBeGreaterThanOrEqual(10)
  })

  it('always sums back to the original amount, across a range of bankroll sizes', () => {
    for (const amount of [0, 1, 3, 37, 46, 530, 1000, 5000]) {
      expect(sum(rackDenomsForAmount(amount))).toBe(amount)
    }
  })

  it('keeps chip count bounded for a very large bankroll (falls back to bigger denoms)', () => {
    const denoms = rackDenomsForAmount(5000)
    expect(sum(denoms)).toBe(5000)
    expect(denoms.length).toBeLessThan(50)
  })

  it('returns an empty stack for zero', () => {
    expect(rackDenomsForAmount(0)).toEqual([])
  })
})
