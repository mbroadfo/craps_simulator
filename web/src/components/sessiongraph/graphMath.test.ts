import { describe, expect, it } from 'vitest'
import { bandKey, betKey, buildChartRows, deltaKey, shooterBoundaryRolls, type GraphPlayer } from './graphMath'

describe('buildChartRows', () => {
  const molly: GraphPlayer = { name: 'Molly', strategy: '3-Point Molly', color: '#4a7fd4', history: [500, 510, 480], atRiskHistory: [0, 10, 5] }
  const linus: GraphPlayer = { name: 'Linus', strategy: 'Pass-Line', color: '#2ecc71', history: [500, 490], atRiskHistory: [0, 5] }

  it('builds one row per roll, keyed by roll number starting at 1', () => {
    const rows = buildChartRows([molly, linus], 3)
    expect(rows.map((r) => r.roll)).toEqual([1, 2, 3])
  })

  it('fills in bankroll, band, bet, and delta for each player present at that roll', () => {
    const rows = buildChartRows([molly, linus], 3)
    expect(rows[1].Molly).toBe(510)
    expect(rows[1][bandKey('Molly')]).toEqual([500, 510]) // bankroll-atRisk to bankroll: 510-10=500 to 510
    expect(rows[1][betKey('Molly')]).toBe(10)
    expect(rows[1][deltaKey('Molly')]).toBe(10) // 510 - 500
  })

  it('leaves a player out of rolls past their own history length (busted out early), not stretched to fill', () => {
    const rows = buildChartRows([molly, linus], 3)
    expect(rows[2].Linus).toBeUndefined()
    expect(rows[2].Molly).toBe(480)
  })

  it('reports zero delta on a player\'s very first roll', () => {
    const rows = buildChartRows([molly], 1)
    expect(rows[0][deltaKey('Molly')]).toBe(0)
  })
})

describe('shooterBoundaryRolls', () => {
  it('always starts with shooter 1 at roll 1', () => {
    expect(shooterBoundaryRolls([])).toEqual([{ roll: 1, shooterNum: 1 }])
  })

  it('places each next shooter at the roll right after their predecessor\'s seven-out', () => {
    // seven-outs at roll-log indices 4 and 9 (0-based) -> shooters 2 and 3
    // begin at 1-based rolls 6 and 11.
    expect(shooterBoundaryRolls([4, 9])).toEqual([
      { roll: 1, shooterNum: 1 },
      { roll: 6, shooterNum: 2 },
      { roll: 11, shooterNum: 3 },
    ])
  })
})
