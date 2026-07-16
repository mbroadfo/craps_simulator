/**
 * One row per seated bot: swatch, name, strategy, a mini bankroll
 * sparkline, and current P&L — click a row to switch the felt's
 * perspective. Replaces the old standalone PlayerSidebar, folded into
 * the Observatory panel alongside session control/leaderboard/etc.
 */
import { sparklinePoints, sparklineTrend } from './sparklinePath'
import './ObservatoryPanel.css'

export interface ObsPlayerRow {
  name: string
  strategy: string
  color: string
  bankroll: number
  /** From netFor() — null until the player has rolled at least once. */
  net: number | null
  /** history[0] — null until the player has rolled at least once. */
  startingBankroll: number | null
  history: number[]
}

function fmtSigned(n: number): string {
  const s = Math.round(n)
  return (s > 0 ? '+' : '') + s.toLocaleString()
}

export function BotRoster({
  roster,
  selectedPlayer,
  onSelectPlayer,
}: {
  roster: ObsPlayerRow[]
  selectedPlayer: string
  onSelectPlayer: (name: string) => void
}) {
  return (
    <div className="obsSection">
      <div className="obsHeader">Bots</div>
      {roster.length === 0 && <div className="obsEmpty">No bots seated</div>}
      {roster.map((p) => {
        const trend = sparklineTrend(p.history)
        return (
          <div
            key={p.name}
            className={'obsRosterRow' + (p.name === selectedPlayer ? ' selected' : '')}
            onClick={() => onSelectPlayer(p.name)}
          >
            <span
              className={'obsSwatch' + (p.name === selectedPlayer ? ' selected' : '')}
              style={{ background: p.color }}
            />
            <div className="obsRosterMain">
              <div className="obsRosterTop">
                <span className="obsRosterName">{p.name}</span>
                <span className={'obsRosterPnl' + (p.net === null ? '' : p.net >= 0 ? ' obsPos' : ' obsNeg')}>
                  {p.net === null ? '—' : fmtSigned(p.net)}
                </span>
              </div>
              {/* Lineup now seats players by strategy name directly
                  (see ObservatoryPanel's DEFAULT_CHECKED), so name and
                  strategy are usually identical — only show this line
                  when they diverge (the plumbing still supports that,
                  it's just not the default anymore). */}
              {p.strategy !== p.name && <div className="obsRosterStrategy">{p.strategy}</div>}
              {/* viewBox fixes an internal 140x14 coordinate system;
                  the CSS width:100% (see .obsSparkline) is what makes
                  it stretch to fill the panel's now-flexible width. */}
              <svg className="obsSparkline" viewBox="0 0 140 14" preserveAspectRatio="none">
                <polyline
                  points={sparklinePoints(p.history, 140, 14)}
                  fill="none"
                  stroke={trend === 'up' ? '#2ecc71' : '#e0564a'}
                  strokeWidth={1.4}
                />
              </svg>
            </div>
          </div>
        )
      })}
    </div>
  )
}
