import { computeRollCounts } from './rollDistributionMath'
import './ObservatoryPanel.css'

/** Session-wide dice-total histogram, vertical bars 2-12 — replaces
 * Strategy Comparison, which was redundant with the Leaderboard. */
export function RollDistribution({ rolls }: { rolls: number[] }) {
  const counts = computeRollCounts(rolls)
  const maxCount = Math.max(1, ...Object.values(counts))

  return (
    <div className="obsSection">
      <div className="obsHeader">Roll Distribution</div>
      {rolls.length === 0 ? (
        <div className="obsEmpty">No rolls yet</div>
      ) : (
        <div className="obsDistChart">
          {Array.from({ length: 11 }, (_, i) => i + 2).map((n) => {
            const count = counts[n]
            const heightPct = (count / maxCount) * 100
            return (
              <div key={n} className="obsDistCol">
                <span className="obsDistCount">{count > 0 ? count : ''}</span>
                <div className="obsDistBarTrack">
                  <div className={'obsDistBar' + (n === 7 ? ' seven' : '')} style={{ height: `${heightPct}%` }} />
                </div>
                <span className="obsDistLabel">{n}</span>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
