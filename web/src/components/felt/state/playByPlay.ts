/**
 * A third independent reducer over the same envelope stream tableReducer
 * (game state) and liveRollLog (per-roll history) consume — turns it
 * into structured commentary for the Observatory panel's Roll Feed.
 * Session-cumulative, capped defensively at MAX_LINES since a session
 * can run for hundreds of rolls. `kind` drives the feed's color coding
 * (seven-outs and losses red, wins green, everything else neutral) —
 * kept separate from `text` so the UI never has to pattern-match
 * rendered strings to figure out how to color a row.
 */
import type { BetNumber, Envelope } from '../../../lib/events'

const MAX_LINES = 300

export type PlayByPlayKind = 'sevenout' | 'win' | 'loss' | 'neutral'

export interface PlayByPlayEntry {
  id: number
  text: string
  kind: PlayByPlayKind
}

function betLabel(betType: string, number: BetNumber): string {
  if (Array.isArray(number)) return `${betType} ${number[0]}-${number[1]}`
  if (number !== null) return `${betType} ${number}`
  return betType
}

function append(lines: PlayByPlayEntry[], entry: PlayByPlayEntry): PlayByPlayEntry[] {
  const next = [...lines, entry]
  return next.length > MAX_LINES ? next.slice(next.length - MAX_LINES) : next
}

export function initialPlayByPlay(): PlayByPlayEntry[] {
  return []
}

export function playByPlayReducer(lines: PlayByPlayEntry[], e: Envelope): PlayByPlayEntry[] {
  switch (e.type) {
    case 'ShooterAssigned':
      return append(lines, { id: e.seq, text: `— ${e.shooter_name} is up —`, kind: 'neutral' })
    case 'DiceRolled':
      return append(lines, { id: e.seq, text: `${e.shooter_name} rolls ${e.dice[0]}-${e.dice[1]} (${e.total})`, kind: 'neutral' })
    case 'PointEstablished':
      return append(lines, { id: e.seq, text: `Point is ${e.point}`, kind: 'neutral' })
    case 'PointHit':
      return append(lines, { id: e.seq, text: `Point made — ${e.point} winners paid`, kind: 'win' })
    case 'SevenOut':
      return append(lines, { id: e.seq, text: 'Seven out', kind: 'sevenout' })
    case 'BetResolved': {
      const label = betLabel(e.bet_type, e.number)
      const won = e.status === 'won'
      const text = won ? `${e.player_name} wins $${e.payout} on ${label}` : `${e.player_name} loses $${e.amount} on ${label}`
      return append(lines, { id: e.seq, text, kind: won ? 'win' : 'loss' })
    }
    case 'SessionFinalized':
      return append(lines, { id: e.seq, text: `Session complete — ${e.session_rolls} rolls`, kind: 'neutral' })
    default:
      return lines
  }
}
