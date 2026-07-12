import { useState } from 'react'
import { THEORY_FREQ } from '../data'

/**
 * Distribution — one horizontal row per number 2-12, a bar
 * proportional to hit count, and a theoretical-frequency tick on each
 * bar track. Genuinely different markup from the other sections (a
 * histogram, not a row list), so it doesn't reuse StatsSection —
 * same collapsible pattern otherwise, collapsed state stays local.
 */
export function DistributionSection({ distribution, totalRolls }: { distribution: Record<number, number>; totalRolls: number }) {
  const [collapsed, setCollapsed] = useState(true)
  const maxCount = Math.max(1, ...Object.values(distribution))

  return (
    <div className={'stSection' + (collapsed ? ' collapsed' : '')} data-testid="stats-section-Distribution">
      <div className="stHeader" onClick={() => setCollapsed((v) => !v)}>
        <span className="stChevron">&#9662;</span>
        Distribution
      </div>
      <div className="stBody">
        <div id="stDist">
          {Array.from({ length: 11 }, (_, i) => i + 2).map((n) => {
            const count = distribution[n] || 0
            const theoryCount = totalRolls > 0 ? (THEORY_FREQ[n] / 36) * totalRolls : 0
            return (
              <div className="stDistRow" key={n}>
                <div className="stDistNum">{n}</div>
                <div className="stDistBarTrack">
                  <div className={'stDistBar' + (n === 7 ? ' seven' : '')} style={{ width: `${(count / maxCount) * 100}%` }} />
                  {totalRolls > 0 && <div className="stDistTick" style={{ left: `${Math.min(100, (theoryCount / maxCount) * 100)}%` }} />}
                </div>
                <div className="stDistCount">{count}</div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
