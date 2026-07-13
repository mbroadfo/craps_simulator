/**
 * A third independent reducer over the same envelope stream tableReducer
 * (game state) and liveRollLog (per-roll history) consume — turns it
 * into human-readable commentary for the roster panel's collapsible
 * play-by-play log. Session-cumulative, capped defensively at
 * MAX_LINES since a session can run for hundreds of rolls.
 */
import type { BetNumber, Envelope } from '../../../lib/events'

const MAX_LINES = 300

function betLabel(betType: string, number: BetNumber): string {
  if (Array.isArray(number)) return `${betType} ${number[0]}-${number[1]}`
  if (number !== null) return `${betType} ${number}`
  return betType
}

function append(lines: string[], line: string): string[] {
  const next = [...lines, line]
  return next.length > MAX_LINES ? next.slice(next.length - MAX_LINES) : next
}

export function initialPlayByPlay(): string[] {
  return []
}

export function playByPlayReducer(lines: string[], e: Envelope): string[] {
  switch (e.type) {
    case 'ShooterAssigned':
      return append(lines, `— ${e.shooter_name} is up —`)
    case 'DiceRolled':
      return append(lines, `${e.shooter_name} rolls ${e.dice[0]}-${e.dice[1]} (${e.total})`)
    case 'PointEstablished':
      return append(lines, `Point is ${e.point}`)
    case 'PointHit':
      return append(lines, `Point made — ${e.point} winners paid`)
    case 'SevenOut':
      return append(lines, 'Seven out')
    case 'BetResolved': {
      const label = betLabel(e.bet_type, e.number)
      const line = e.status === 'won' ? `${e.player_name} wins $${e.payout} on ${label}` : `${e.player_name} loses $${e.amount} on ${label}`
      return append(lines, line)
    }
    case 'SessionFinalized':
      return append(lines, `Session complete — ${e.session_rolls} rolls`)
    default:
      return lines
  }
}
