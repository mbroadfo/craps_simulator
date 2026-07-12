/**
 * Data tables ported verbatim from prototype/parametric-felt.html.
 */
import type { HopKind } from './layout'

// Chip placement is a DEV TOOL for validating bet-position coordinates,
// not the real interaction model — the live felt places chips from
// BetPlaced/BetResolved events, never clicks (Step 3, not this step).
// Chip denominations — standard casino colors, edge-spot colors per the
// reference photos (assets/*.png chip-rail shots). `fill`/`edge` are the
// solid on-felt/rail chip colors; `ring` is the accent color used by the
// picker's white-body poker-chip icon (ChipFace) — same hue as fill
// except $1, which stays a white/grey solid chip on the felt but wants a
// distinct blue ring in the icon (matching the reference chip-icon set).
export interface Denom {
  value: number
  label: string
  fill: string
  edge: string
  ring: string
}
export const DENOMS: Denom[] = [
  { value: 1, label: '$1', fill: '#d4d4d4', edge: '#8a8a8a', ring: '#2a5ca8' },
  { value: 5, label: '$5', fill: '#c0392b', edge: '#ffffff', ring: '#c0392b' },
  { value: 25, label: '$25', fill: '#27ae60', edge: '#ffffff', ring: '#1f8b4c' },
  { value: 100, label: '$100', fill: '#2c2c2c', edge: '#ffffff', ring: '#2c2c2c' },
  { value: 500, label: '$500', fill: '#6c3483', edge: '#c9a84c', ring: '#6c3483' },
]

// Bankroll lives as an explicit chip rack (denom -> count), not a dollar
// number — $500 dealt as 2x$100 + 8x$25 + 20x$5 (deliberately textured,
// not a single $500 chip), so a plain greedy dollar->chip breakdown
// wouldn't reproduce it.
export function startingRack(): Record<number, number> {
  return { 1: 0, 5: 20, 25: 8, 100: 2, 500: 0 }
}

// Engine truth for the readout (exact values from craps/edge.py)
export const EDGE = {
  place: { 4: '6.67%', 5: '4.00%', 6: '1.52%', 8: '1.52%', 9: '4.00%', 10: '6.67%' } as Record<number, string>,
  buy_on_win: { 4: '1.67%', 5: '1.33%', 9: '1.33%', 10: '1.67%' } as Record<number, string>,
  hopEasy: '11.11%',
  hopHard: '13.89%',
  horn: '12.50%',
  world: '13.33%',
  anySeven: '16.67%',
  anyCraps: '11.11%',
  atsAll: '7.4644%',
  atsTS: '7.7613%',
  hard68: '9.09%',
  hard410: '11.11%',
}

export interface HopStyle {
  fill: string
  ring: string
  text: string
  pays: string
  payFill: string
}
export const HOP_STYLE: Record<HopKind, HopStyle> = {
  hard: { fill: '#2a1c08', ring: '#e8a04a', text: '#f3ce74', pays: '30:1', payFill: '#f3ce74' },
  easy: { fill: '#111214', ring: '#8a8171', text: '#d8cfae', pays: '15:1', payFill: '#8a8171' },
  seven: { fill: '#2a0f0c', ring: '#d95f4c', text: '#e8938a', pays: '15:1', payFill: '#efe7d3' },
}
export const HOP_FACE: Record<HopKind, string> = { hard: '#e8a04a', easy: '#efe7d3', seven: '#efe7d3' }

// dice-total theoretical frequency, out of 36
export const THEORY_FREQ: Record<number, number> = { 2: 1, 3: 2, 4: 3, 5: 4, 6: 5, 7: 6, 8: 5, 9: 4, 10: 3, 11: 2, 12: 1 }

export type RollType = 'point-set' | 'point-hit' | 'seven-out' | 'hardway' | 'neutral'
export const ROLL_COLORS: Record<RollType, string> = {
  'point-set': '#4a7fd4',
  'point-hit': '#3fae74',
  'seven-out': '#e05a48',
  hardway: '#e8a04a',
  neutral: '#8a8171',
}

// A roll that's BOTH the point and hard (e.g. point=8, rolls 4-4)
// counts as point-hit — the line result outranks how the number was
// made.
export function classifyRoll(d1: number, d2: number, pointBefore: number | null): RollType {
  const total = d1 + d2
  if (pointBefore != null && total === 7) return 'seven-out'
  if (pointBefore != null && total === pointBefore) return 'point-hit'
  if (pointBefore == null && [4, 5, 6, 8, 9, 10].includes(total)) return 'point-set'
  if (d1 === d2 && [4, 6, 8, 10].includes(total)) return 'hardway'
  return 'neutral'
}
