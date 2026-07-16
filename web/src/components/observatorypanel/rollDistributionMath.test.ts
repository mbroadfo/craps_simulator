import { describe, expect, it } from 'vitest'
import { computeRollCounts } from './rollDistributionMath'

describe('computeRollCounts', () => {
  it('returns a zeroed count for every total 2-12 with no rolls', () => {
    const counts = computeRollCounts([])
    expect(Object.keys(counts)).toHaveLength(11)
    for (let n = 2; n <= 12; n++) expect(counts[n]).toBe(0)
  })

  it('tallies each total', () => {
    const counts = computeRollCounts([7, 7, 4, 11, 7, 2])
    expect(counts[7]).toBe(3)
    expect(counts[4]).toBe(1)
    expect(counts[11]).toBe(1)
    expect(counts[2]).toBe(1)
    expect(counts[6]).toBe(0)
  })

  it('ignores out-of-range values defensively', () => {
    const counts = computeRollCounts([1, 13, 7])
    expect(counts[7]).toBe(1)
    expect(Object.values(counts).reduce((a, b) => a + b, 0)).toBe(1)
  })
})
