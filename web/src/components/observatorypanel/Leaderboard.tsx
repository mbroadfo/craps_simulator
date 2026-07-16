import type { ObsPlayerRow } from './BotRoster'
import { rankPlayers } from './leaderboardMath'
import './ObservatoryPanel.css'

function fmtSigned(n: number): string {
  const s = Math.round(n)
  return (s > 0 ? '+' : '') + s.toLocaleString()
}

export function Leaderboard({ roster }: { roster: ObsPlayerRow[] }) {
  const rows = rankPlayers(roster)

  return (
    <div className="obsSection">
      <div className="obsHeader">Leaderboard</div>
      {rows.length === 0 && <div className="obsEmpty">No results yet</div>}
      {rows.map((r) => (
        <div key={r.name} className={'obsLeaderRow' + (r.rank === 1 ? ' leader' : '')}>
          <span className="obsLeaderRank">{r.rank}</span>
          <span className="obsLeaderName">{r.name}</span>
          <span className={'obsLeaderPnl' + (r.net >= 0 ? ' obsPos' : ' obsNeg')}>{fmtSigned(r.net)}</span>
          <span className={'obsLeaderRoi' + (r.roiPct >= 0 ? ' obsPos' : ' obsNeg')}>
            {r.roiPct >= 0 ? '+' : ''}
            {r.roiPct.toFixed(1)}%
          </span>
        </div>
      ))}
    </div>
  )
}
