/**
 * When two bets resolve on the same roll near the same felt position
 * (e.g. Pass Line + Pass Line Odds, only ~20-40px apart), their toasts
 * land almost exactly on top of each other and become unreadable.
 * Shared by both useFeltDevState's pushToast (testAllBets can fire
 * several at once) and useFeltLiveState (a single roll can resolve
 * several of one player's bets) so live and dev mode stack the same
 * way — stagger a new toast upward past any still-visible toast whose
 * anchor is within radius of it.
 */
import type { Toast } from '../types'

const PROXIMITY_RADIUS_X = 70
// Generous enough to still recognize a toast several stacks up as
// "the same pile" rather than a coincidentally-aligned unrelated
// zone — narrower than STACK_OFFSET * a realistic max stack height
// would false-negative on toast 3+ (each stacked toast drifts
// STACK_OFFSET further from the original target y).
const PROXIMITY_RADIUS_Y = 240
const STACK_OFFSET = 46

export function stackedToastY(existing: Toast[], x: number, y: number): number {
  const nearby = existing.filter((t) => Math.abs(t.x - x) < PROXIMITY_RADIUS_X && t.y > y - PROXIMITY_RADIUS_Y)
  if (nearby.length === 0) return y

  // Anchor to the highest (smallest-y) nearby toast and place STACK_OFFSET
  // above *that* — not a flat `y - count * STACK_OFFSET` off this toast's
  // own raw target. That flat version assumed every "nearby" toast started
  // at the exact same y (true for its original case: several dev-tool test
  // toasts fired at one identical coordinate), so subtracting a fixed
  // amount from a shared baseline produced an evenly-spaced stack. It
  // breaks the moment two zones have their own small natural y-gap before
  // stacking even starts (Pass Line vs Pass Line Odds, 37px apart): the new
  // toast's raw target is already partway up from the old one, so
  // subtracting another flat 46px overshoots past it, landing only ~9px
  // away instead of clearing it — the exact "toasts overlap" bug this
  // anchors against.
  const highest = Math.min(y, ...nearby.map((t) => t.y))
  return highest - STACK_OFFSET
}
