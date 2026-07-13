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
  const nearby = existing.filter(
    (t) => Math.abs(t.x - x) < PROXIMITY_RADIUS_X && t.y <= y + STACK_OFFSET && t.y > y - PROXIMITY_RADIUS_Y,
  ).length
  return y - nearby * STACK_OFFSET
}
