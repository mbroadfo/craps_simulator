/**
 * The right-of-shooter-history panel that replaces the old Observatory
 * harness's lineup + player-select controls. App-level plumbing (table
 * lifecycle, api.listStrategies) — deliberately outside web/src/
 * components/felt/, which only knows how to render a felt, not how a
 * table gets created. Two modes via `hasTable`: a lineup builder
 * before the table exists, a live roster + collapsible play-by-play
 * log once it's running.
 */
import { useEffect, useRef, useState } from 'react'
import './RosterPanel.css'
import { api, type PlayerSpec } from '../../lib/api'

const SEAT_POOL = ['Molly', 'Crosstopher', 'Linus', 'Priya']
const DEFAULT_STRATEGY: Record<string, string> = {
  Molly: '3-Point Molly',
  Crosstopher: 'Iron Cross',
  Linus: 'Pass-Line',
}

interface Seat {
  name: string
  enabled: boolean
  strategy: string
}

function fmtMoney(n: number): string {
  return `$${Math.round(n).toLocaleString()}`
}
function fmtSigned(n: number): string {
  const s = Math.round(n)
  return (s > 0 ? '+' : '') + s.toLocaleString()
}

export interface RosterRow {
  name: string
  strategy: string
  bankroll: number
  net: number | null
}

export function RosterPanel({
  hasTable,
  creating,
  error,
  onCreateAndStart,
  rosterRows,
  selectedPlayer,
  onSelectPlayer,
  playByPlay,
}: {
  hasTable: boolean
  creating: boolean
  error: string | null
  onCreateAndStart: (lineup: PlayerSpec[]) => void
  rosterRows: RosterRow[]
  selectedPlayer: string
  onSelectPlayer: (name: string) => void
  playByPlay: string[]
}) {
  const [strategies, setStrategies] = useState<string[]>([])
  const [seats, setSeats] = useState<Seat[]>(() =>
    SEAT_POOL.map((name) => ({ name, enabled: name in DEFAULT_STRATEGY, strategy: DEFAULT_STRATEGY[name] ?? '' })),
  )

  useEffect(() => {
    api.listStrategies().then((list) => {
      setStrategies(list)
      setSeats((prev) => prev.map((s) => (s.strategy ? s : { ...s, strategy: list[0] ?? '' })))
    })
  }, [])

  const canCreate = seats.some((s) => s.enabled && s.strategy)

  if (!hasTable) {
    return (
      <div className="rosterPanel">
        <div className="rosterHeader">Lineup</div>
        {seats.map((seat, i) => (
          <div key={seat.name} className="seatRow">
            <label className="seatCheck">
              <input
                type="checkbox"
                checked={seat.enabled}
                onChange={(e) => setSeats((prev) => prev.map((s, j) => (j === i ? { ...s, enabled: e.target.checked } : s)))}
              />
              {seat.name}
            </label>
            <select
              className="seatStrategy"
              value={seat.strategy}
              disabled={!seat.enabled}
              onChange={(e) => setSeats((prev) => prev.map((s, j) => (j === i ? { ...s, strategy: e.target.value } : s)))}
            >
              {strategies.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </div>
        ))}
        {error && <div className="rosterError">{error}</div>}
        <button
          className="rosterCreateBtn"
          disabled={creating || !canCreate}
          onClick={() => onCreateAndStart(seats.filter((s) => s.enabled && s.strategy).map((s) => ({ name: s.name, strategy: s.strategy })))}
        >
          {creating ? 'Starting…' : 'Create + Start'}
        </button>
      </div>
    )
  }

  return (
    <div className="rosterPanel">
      <div className="rosterHeader">Roster</div>
      {rosterRows.map((p) => (
        <div key={p.name} className={'rosterRow' + (p.name === selectedPlayer ? ' selected' : '')} onClick={() => onSelectPlayer(p.name)}>
          <div className="rosterRowTop">
            <span className="rosterRowName">{p.name}</span>
            <span className="rosterRowBankroll">{fmtMoney(p.bankroll)}</span>
          </div>
          <div className="rosterRowBottom">
            <span className="rosterRowStrategy">{p.strategy}</span>
            <span className={'rosterRowNet' + (p.net !== null ? (p.net >= 0 ? ' pos' : ' neg') : '')}>{p.net === null ? '—' : fmtSigned(p.net)}</span>
          </div>
        </div>
      ))}
      <PlayByPlay lines={playByPlay} />
    </div>
  )
}

function PlayByPlay({ lines }: { lines: string[] }) {
  const [collapsed, setCollapsed] = useState(false)
  const listRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!collapsed && listRef.current) listRef.current.scrollTop = listRef.current.scrollHeight
  }, [lines, collapsed])

  return (
    <div className={'playByPlay' + (collapsed ? ' collapsed' : '')}>
      <div className="playByPlayHeader" onClick={() => setCollapsed((v) => !v)}>
        <span className="pbpChevron">&#9662;</span>
        Play by Play
      </div>
      {!collapsed && (
        <div className="playByPlayList" ref={listRef}>
          {lines.map((line, i) => (
            <div key={i} className="pbpLine">
              {line}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
