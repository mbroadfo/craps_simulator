/**
 * The horizontal band between the felt and the session graph: the
 * lineup builder before a table exists, and once it's running, the
 * Play/Pause, Roll, Turbo, and Reset controls. The perspective picker
 * used to live here too (a "Perspective" dropdown) — moved back out
 * to PlayerSidebar (a proper vertical sidebar next to the felt,
 * showing bankroll per row) since a single dropdown wasted the
 * stripe's horizontal room for very little payoff.
 */
import { useEffect, useState } from 'react'
import './ControlStripe.css'
import type { PlayerSpec, TableSnapshot } from '../../lib/api'
import { api } from '../../lib/api'

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

export function ControlStripe({
  hasTable,
  creating,
  error,
  onCreateAndStart,
  onReset,
  sessionState,
  onPauseResume,
  onTurbo,
  turboOn,
  onStep,
}: {
  hasTable: boolean
  creating: boolean
  error: string | null
  onCreateAndStart: (lineup: PlayerSpec[]) => void
  onReset: () => void
  sessionState: TableSnapshot['state'] | null
  onPauseResume: () => void
  onTurbo: () => void
  turboOn: boolean
  onStep: () => void
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

  if (!hasTable) {
    const canCreate = seats.some((s) => s.enabled && s.strategy)
    return (
      <div className="controlStripe">
        <div className="stripeSeats">
          {seats.map((seat, i) => (
            <label key={seat.name} className="stripeSeat">
              <input
                type="checkbox"
                checked={seat.enabled}
                onChange={(e) => setSeats((prev) => prev.map((s, j) => (j === i ? { ...s, enabled: e.target.checked } : s)))}
              />
              {seat.name}
              <select
                className="stripeSeatStrategy"
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
            </label>
          ))}
        </div>
        {error && <div className="stripeError">{error}</div>}
        <button
          className="stripeCreateBtn"
          disabled={creating || !canCreate}
          onClick={() => onCreateAndStart(seats.filter((s) => s.enabled && s.strategy).map((s) => ({ name: s.name, strategy: s.strategy })))}
        >
          {creating ? 'Starting…' : 'Start'}
        </button>
      </div>
    )
  }

  const disabled = sessionState === null || sessionState === 'finished' || sessionState === 'stopped'
  const paused = sessionState === 'paused'

  return (
    <div className="controlStripe">
      <div className="stripeControls">
        <button className="iconBtn" title={paused ? 'Play' : 'Pause'} disabled={disabled} onClick={onPauseResume}>
          {paused ? '▶' : '⏸'}
        </button>
        <button className="iconBtn" title="Roll — advance one roll, then stay paused" disabled={!paused} onClick={onStep}>
          {'🎲'}
        </button>
        <button className={'iconBtn' + (turboOn ? ' primary' : '')} title="Turbo — no roll delay" disabled={disabled} onClick={onTurbo}>
          {'⏩'}
        </button>
      </div>
      <button className="stripeCreateBtn" title="Reset — end this game and start a new one" onClick={onReset}>
        Reset
      </button>
    </div>
  )
}
