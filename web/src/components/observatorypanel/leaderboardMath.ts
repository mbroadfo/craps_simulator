/**
 * Ranks seated players by current net (bankroll minus starting
 * bankroll) for the Observatory panel's Leaderboard and Strategy
 * Comparison sections. Pure and separately unit-tested, matching the
 * repo's established pattern (graphMath.ts, chipDecompose.ts).
 */
export interface LeaderboardInput {
  name: string
  /** From netFor() in useFeltLiveState.ts — null until the player has rolled at least once. */
  net: number | null
  /** history[0] — null/omitted players with no history yet are excluded, not divided-by-zero. */
  startingBankroll: number | null
}

export interface LeaderboardRow {
  rank: number
  name: string
  net: number
  roiPct: number
}

export function rankPlayers(rows: LeaderboardInput[]): LeaderboardRow[] {
  return rows
    .filter((r) => r.net !== null && r.startingBankroll !== null && r.startingBankroll !== 0)
    .map((r) => ({ name: r.name, net: r.net as number, roiPct: ((r.net as number) / (r.startingBankroll as number)) * 100 }))
    .sort((a, b) => b.net - a.net)
    .map((r, i) => ({ rank: i + 1, ...r }))
}
