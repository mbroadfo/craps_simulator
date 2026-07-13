/**
 * A lean, single-purpose right-side sidebar: one row per seated
 * player showing name, strategy, and live bankroll/net, click to
 * switch the felt's perspective. Second attempt at this — the first
 * (RosterPanel) mixed in a lineup builder and a play-by-play log and
 * got cut entirely for it ("that whole right side is annoying").
 * This one does exactly one job.
 */
import './PlayerSidebar.css'

export interface PlayerSidebarRow {
  name: string
  strategy: string
  bankroll: number
  net: number | null
}

function fmtMoney(n: number): string {
  return `$${Math.round(n).toLocaleString()}`
}
function fmtSigned(n: number): string {
  const s = Math.round(n)
  return (s > 0 ? '+' : '') + s.toLocaleString()
}

export function PlayerSidebar({
  roster,
  selectedPlayer,
  onSelectPlayer,
}: {
  roster: PlayerSidebarRow[]
  selectedPlayer: string
  onSelectPlayer: (name: string) => void
}) {
  if (roster.length === 0) return null

  return (
    <div className="playerSidebar">
      {roster.map((p) => (
        <div
          key={p.name}
          className={'playerSidebarRow' + (p.name === selectedPlayer ? ' selected' : '')}
          onClick={() => onSelectPlayer(p.name)}
        >
          <div className="playerSidebarTop">
            <span className="playerSidebarName">{p.name}</span>
            <span className="playerSidebarBankroll">{fmtMoney(p.bankroll)}</span>
          </div>
          <div className="playerSidebarBottom">
            <span className="playerSidebarStrategy">{p.strategy}</span>
            <span className={'playerSidebarNet' + (p.net !== null ? (p.net >= 0 ? ' pos' : ' neg') : '')}>
              {p.net === null ? '—' : fmtSigned(p.net)}
            </span>
          </div>
        </div>
      ))}
    </div>
  )
}
