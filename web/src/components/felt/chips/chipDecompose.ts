/**
 * Turns a real dollar bet amount (Step 3, spectator mode) into a
 * plausible stack of casino-chip denominations for ChipStackLayer to
 * draw. ChipFace's `labelOverride` already decouples the drawn number
 * from a chip's color (see ChipFace.tsx), and ChipStackLayer already
 * sums a zone's `denoms` and labels only the top chip with that total
 * — so as long as this decomposition sums back to `amount`, the
 * existing rendering pipeline shows the real dollar figure untouched.
 */
import { DENOMS } from '../data'

export function chipDenomsForAmount(amount: number): number[] {
  const values = [...DENOMS].map((d) => d.value).sort((a, b) => b - a)
  let remaining = Math.round(amount)
  const denoms: number[] = []
  for (const value of values) {
    while (remaining >= value) {
      denoms.push(value)
      remaining -= value
    }
  }
  return denoms
}

// Ascending, capped per denomination — a $500 bankroll should look
// like a real player's rack (mostly $5/$25, a little $100, hardly
// ever a single $500 chip standing in for the whole pile), not the
// most efficient possible stack. chipDenomsForAmount's plain greedy
// (largest-first, no cap) is right for a labeled on-felt bet stack —
// the label already carries the exact total, so chip count doesn't
// matter — but it's wrong for the *rack*, which has no label at all:
// a $500+$100 pile barely visibly changes for a typical $10-$50 win,
// which is exactly the "I don't see the payout" complaint this fixes.
const RACK_TIER_CAPS: [value: number, cap: number][] = [
  [1, 4],
  [5, 6],
  [25, 6],
  [100, 4],
]

export function rackDenomsForAmount(amount: number): number[] {
  let remaining = Math.round(amount)
  const denoms: number[] = []
  for (const [value, cap] of RACK_TIER_CAPS) {
    const count = Math.min(cap, Math.floor(remaining / value))
    for (let n = 0; n < count; n++) denoms.push(value)
    remaining -= count * value
  }
  // Whatever the capped texture pass above couldn't place (either it
  // hit every cap, or the leftover falls between tiers) gets swept up
  // by the same plain greedy decomposition bet stacks use — guarantees
  // this always sums back to `amount` exactly, for any amount.
  denoms.push(...chipDenomsForAmount(remaining))
  return denoms
}
