/** 4/6/8/10 made as a matching pair are hardways in craps table lingo — everything else is just its sum. */
const HARDWAY_SUMS = new Set([4, 6, 8, 10])

export function formatRollSum(dice: [number, number] | null): string {
  if (!dice) return '—'
  const [d1, d2] = dice
  const sum = d1 + d2
  return d1 === d2 && HARDWAY_SUMS.has(sum) ? `${sum}H` : String(sum)
}
