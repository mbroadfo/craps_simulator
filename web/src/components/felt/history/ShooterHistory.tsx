import { ROLL_COLORS } from '../data'
import { useFeltState } from '../state/FeltStateContext'
import { currentShooterRolls } from './currentShooterRolls'

/**
 * Bare vertical list of colored roll totals (renderShooterHistory in
 * the prototype) — no card, no border, no title. Oldest at top, newest
 * appended at the bottom. Resets to show only the current shooter's
 * rolls the roll after a seven-out — rollHistory itself stays intact
 * (session stats stay cumulative once they exist), only this filtered
 * view resets. Deliberately not a `r.shooter === shooterNum` filter —
 * see currentShooterRolls.ts for why that throws the seven-out roll
 * away the instant it happens instead of showing it.
 */
export function ShooterHistory() {
  const { rollHistory } = useFeltState()
  const current = currentShooterRolls(rollHistory)

  return (
    <div className="shooterHistory">
      <div id="shList">
        {current.map((r, i) => (
          <div key={i} className="shRoll" style={{ color: ROLL_COLORS[r.type] }}>
            {r.total}
          </div>
        ))}
      </div>
    </div>
  )
}
