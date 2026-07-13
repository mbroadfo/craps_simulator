/**
 * A second, independent reducer over the same envelope stream
 * tableReducer.ts consumes (Step 3, spectator mode) — deliberately
 * NOT a change to that shared, fixture-gated reducer. TableState only
 * keeps the latest dice roll plus a session-aggregate rollCounts, not
 * a per-roll sequence; ShooterHistory (and, through it, the felt's
 * existing Distribution/Session stats) needs the sequence.
 *
 * Rolls are never cleared — session-cumulative, exactly like the
 * dev-tool's own rollHistory (see useFeltDevState.ts) — each record
 * just carries its shooter's index, and ShooterHistory's existing
 * per-shooter filter is what makes the display look like it resets on
 * a new shooter.
 *
 * classifyRoll needs "the point in effect before this roll" — and
 * DiceRolled.point already *is* that value, not the result of the
 * roll: table_runner.py's roll_once() calls engine.roll_dice() (which
 * publishes DiceRolled off the still-previous game_state.point/phase)
 * strictly before engine.resolve_bets() runs and actually updates
 * game_state.point / publishes PointEstablished/PointHit/SevenOut. An
 * earlier version of this reducer cached each roll's e.point and fed
 * it in as pointBefore on the *next* call — one roll late, since
 * e.point was already the right value for the roll it arrived on.
 * That produced visibly nonsensical shooter-history colors (a point
 * showing as freshly "set" a roll after it actually was, hardways/
 * seven-outs misjudged against a stale number). Use e.point directly;
 * no state needs to be carried across calls at all.
 */
import type { Envelope } from '../../../lib/events'
import { classifyRoll } from '../data'
import type { RollRecord } from '../types'

export interface RollLogState {
  rolls: RollRecord[]
}

export function initialRollLogState(): RollLogState {
  return { rolls: [] }
}

export function rollLogReducer(state: RollLogState, e: Envelope): RollLogState {
  if (e.type !== 'DiceRolled') return state
  const [d1, d2] = e.dice
  const type = classifyRoll(d1, d2, e.point)
  const record: RollRecord = { shooter: e.shooter_index, d1, d2, total: e.total, type }
  return { rolls: [...state.rolls, record] }
}
