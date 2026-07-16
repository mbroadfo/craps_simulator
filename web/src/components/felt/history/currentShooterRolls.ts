import type { RollRecord } from '../types'

/**
 * The rolls to show for "the current shooter" — deliberately not a
 * filter on the live shooter index (tableState.shooterIndex), which
 * already reflects the *next* shooter by the time a seven-out reaches
 * the frontend: ShooterAssigned is published in the same roll_once()
 * call as SevenOut (craps_engine.py's handle_post_roll() calls
 * assign_next_shooter() right after publishing SevenOut), so
 * filtering by "shooter === current shooter index" throws the just-
 * rolled seven-out away the instant it arrives — it was recorded
 * under the *old* shooter's index, which no longer matches by the
 * time React renders. Instead, find the boundary directly from the
 * roll sequence itself: the seven-out that ended the previous
 * shooter (if any) stays visible as the last roll of its own group
 * until the next roll (the new shooter's first) actually arrives.
 */
export function currentShooterRolls(rollHistory: RollRecord[]): RollRecord[] {
  if (rollHistory.length === 0) return []

  const lastIndex = rollHistory.length - 1
  const searchEnd = rollHistory[lastIndex].type === 'seven-out' ? lastIndex - 1 : lastIndex

  let boundary = -1
  for (let i = searchEnd; i >= 0; i--) {
    if (rollHistory[i].type === 'seven-out') {
      boundary = i
      break
    }
  }

  return rollHistory.slice(boundary + 1)
}
