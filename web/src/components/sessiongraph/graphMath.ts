/**
 * Pure data-shaping for the session graph — kept separate from
 * SessionGraph.tsx so it's unit-testable without a DOM, matching the
 * project's established pattern (computeSidebarScale, chipDenomsForAmount,
 * feltZoneFor all do the same split). Recharts owns the actual pixel
 * geometry now; this module only builds the one-row-per-roll data
 * array + derived keys recharts' dataKey lookups need.
 */
export interface GraphPlayer {
  name: string
  strategy: string
  color: string
  history: number[]
  /** at-risk amount over time, index-aligned with history. */
  atRiskHistory: number[]
}

export type ChartRow = {
  roll: number
} & Record<string, number | [number, number] | undefined>

export const bandKey = (name: string): string => `${name}__band`
export const betKey = (name: string): string => `${name}__bet`
export const deltaKey = (name: string): string => `${name}__delta`

/**
 * One row per roll (1-indexed, matching the reference chart's x-axis)
 * across the shared `totalRolls` domain — a player whose history ends
 * early (busted out) simply has no entries past their own length,
 * rather than being stretched to fill the rest.
 */
export function buildChartRows(players: GraphPlayer[], totalRolls: number): ChartRow[] {
  const rows: ChartRow[] = []
  for (let i = 0; i < totalRolls; i++) {
    const row: ChartRow = { roll: i + 1 }
    for (const p of players) {
      if (i >= p.history.length) continue
      const bankroll = p.history[i]
      const atRisk = p.atRiskHistory[i] ?? 0
      row[p.name] = bankroll
      // Below the line, not above: the shaded band is "how much of
      // this bankroll is currently exposed on active bets" (downside
      // risk), not a hypothetical upside if every active bet wins.
      row[bandKey(p.name)] = [bankroll - atRisk, bankroll]
      row[betKey(p.name)] = atRisk
      row[deltaKey(p.name)] = i > 0 && i - 1 < p.history.length ? bankroll - p.history[i - 1] : 0
    }
    rows.push(row)
  }
  return rows
}

export interface ShooterBoundary {
  roll: number
  shooterNum: number
}

/**
 * Shooter 1 starts at roll 1; shooter N (N>1) starts the roll right
 * after the (N-1)th seven-out — sevenOutIndices are 0-based positions
 * into the roll log, so the next shooter's first roll is at
 * `index + 2` in 1-based roll numbering.
 */
export function shooterBoundaryRolls(sevenOutIndices: number[]): ShooterBoundary[] {
  const boundaries: ShooterBoundary[] = [{ roll: 1, shooterNum: 1 }]
  sevenOutIndices.forEach((i, idx) => {
    boundaries.push({ roll: i + 2, shooterNum: idx + 2 })
  })
  return boundaries
}
