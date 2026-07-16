import { describe, expect, it } from 'vitest'
import { rankPlayers } from './leaderboardMath'

describe('rankPlayers', () => {
  it('ranks by net descending', () => {
    const rows = rankPlayers([
      { name: 'A', net: 10, startingBankroll: 1000 },
      { name: 'B', net: 142, startingBankroll: 1000 },
      { name: 'C', net: -50, startingBankroll: 1000 },
    ])
    expect(rows.map((r) => r.name)).toEqual(['B', 'A', 'C'])
    expect(rows.map((r) => r.rank)).toEqual([1, 2, 3])
  })

  it('computes ROI as a percentage of starting bankroll', () => {
    const rows = rankPlayers([{ name: 'A', net: 142, startingBankroll: 1000 }])
    expect(rows[0].roiPct).toBeCloseTo(14.2)
  })

  it('excludes players with no history yet (net or startingBankroll null)', () => {
    const rows = rankPlayers([
      { name: 'A', net: null, startingBankroll: null },
      { name: 'B', net: 50, startingBankroll: 1000 },
    ])
    expect(rows.map((r) => r.name)).toEqual(['B'])
  })

  it('excludes a zero starting bankroll to avoid divide-by-zero', () => {
    const rows = rankPlayers([{ name: 'A', net: 50, startingBankroll: 0 }])
    expect(rows).toEqual([])
  })

  it('returns an empty list for no players', () => {
    expect(rankPlayers([])).toEqual([])
  })
})
