import { ROLL_COLORS } from '../data'
import { useFeltState } from '../state/FeltStateContext'

/**
 * Bare vertical list of colored roll totals (renderShooterHistory in
 * the prototype) — no card, no border, no title. Oldest at top, newest
 * appended at the bottom. Resets to show only the current shooter's
 * rolls (filtered by shooter number) the roll after a seven-out —
 * rollHistory itself stays intact (session stats stay cumulative once
 * they exist), only this filtered view resets.
 */
export function ShooterHistory() {
  const { rollHistory, shooterNum } = useFeltState()
  const current = rollHistory.filter((r) => r.shooter === shooterNum)

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
