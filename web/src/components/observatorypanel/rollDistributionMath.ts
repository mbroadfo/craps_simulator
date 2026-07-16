/** Session-wide dice-total histogram (2-12) for the Observatory panel's Roll Distribution chart. */
export function computeRollCounts(totals: number[]): Record<number, number> {
  const counts: Record<number, number> = {}
  for (let n = 2; n <= 12; n++) counts[n] = 0
  for (const t of totals) {
    if (t >= 2 && t <= 12) counts[t]++
  }
  return counts
}
