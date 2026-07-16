/**
 * The right-side dashboard for Bot Observatory mode — replaces both
 * ControlStripe (lineup builder + Play/Roll/Turbo/Reset) and
 * PlayerSidebar (name/strategy/bankroll rows) with one panel in a
 * distinct Georgia/gold visual language. Single Player mode (click-
 * to-bet, EV assistant) from the original spec is deliberately not
 * built here — this simulator has no backend path for a human to
 * place a real bet, and building one is out of scope for this pass.
 *
 * ControlRail (hamburger/Start/Roll/Play/Turbo/Reset) is fixed —
 * always visible regardless of scroll or whether a table exists yet
 * (see .railControls in ObservatoryPanel.css). It's rendered here as
 * a sibling of the scrolling panel content, not nested inside it — a
 * fixed-position element ignores its DOM ancestor's layout entirely,
 * so where it's mounted only matters for the React tree, not the
 * page. The `seats` lineup array itself is owned by App.tsx (not
 * local state here) since ControlRail's Start button needs to read it
 * too — this component just renders the lineup and reports toggles
 * upward.
 */
import type { TableSnapshot } from '../../lib/api'
import type { PlayByPlayEntry } from '../felt/state/playByPlay'
import { BotRoster, type ObsPlayerRow } from './BotRoster'
import { ControlRail } from './ControlRail'
import { CurrentRoll } from './CurrentRoll'
import { Leaderboard } from './Leaderboard'
import './ObservatoryPanel.css'
import { RollDistribution } from './RollDistribution'
import { RollFeed } from './RollFeed'

export interface Seat {
  name: string
  enabled: boolean
}

export function ObservatoryPanel({
  hasTable,
  seats,
  onToggleSeat,
  onSelectAll,
  onClearAll,
  numShooters,
  onNumShootersChange,
  canStart,
  creating,
  error,
  onStart,
  sessionState,
  onPauseResume,
  onStep,
  onReset,
  speed,
  onSpeedChange,
  roster,
  selectedPlayer,
  onSelectPlayer,
  feed,
  rolls,
  dice,
}: {
  hasTable: boolean
  seats: Seat[]
  onToggleSeat: (index: number) => void
  onSelectAll: () => void
  onClearAll: () => void
  numShooters: number
  onNumShootersChange: (n: number) => void
  canStart: boolean
  creating: boolean
  error: string | null
  onStart: () => void
  sessionState: TableSnapshot['state'] | null
  onPauseResume: () => void
  onStep: () => void
  onReset: () => void
  speed: number
  onSpeedChange: (speed: number) => void
  roster: ObsPlayerRow[]
  selectedPlayer: string
  onSelectPlayer: (name: string) => void
  feed: PlayByPlayEntry[]
  rolls: number[]
  dice: [number, number] | null
}) {
  const controlRail = (
    <ControlRail
      hasTable={hasTable}
      canStart={canStart}
      creating={creating}
      error={error}
      onStart={onStart}
      sessionState={sessionState}
      onPauseResume={onPauseResume}
      onStep={onStep}
      onReset={onReset}
      speed={speed}
      onSpeedChange={onSpeedChange}
    />
  )

  if (!hasTable) {
    return (
      <>
        {controlRail}
        <div className="observatoryPanel">
          <div className="obsSection">
            <div className="obsHeaderRow">
              <div className="obsHeader">Lineup</div>
              <div className="obsBulkRow">
                <button className="obsBulkBtn" onClick={onSelectAll}>
                  Select All
                </button>
                <button className="obsBulkBtn" onClick={onClearAll}>
                  Clear All
                </button>
              </div>
            </div>
            {seats.map((seat, i) => (
              <label key={seat.name} className="obsSeat">
                <input type="checkbox" checked={seat.enabled} onChange={() => onToggleSeat(i)} />
                {seat.name}
              </label>
            ))}
            <div className="obsShootersRow">
              <span className="obsLabel">Shooters</span>
              <input
                className="obsShootersInput"
                type="number"
                min={1}
                max={1000}
                value={numShooters}
                onChange={(e) => onNumShootersChange(Math.max(1, Math.min(1000, Number(e.target.value))))}
              />
            </div>
          </div>
        </div>
      </>
    )
  }

  return (
    <>
      {controlRail}
      <div className="observatoryPanel">
        <CurrentRoll dice={dice} />
        <BotRoster roster={roster} selectedPlayer={selectedPlayer} onSelectPlayer={onSelectPlayer} />
        <Leaderboard roster={roster} />
        <RollDistribution rolls={rolls} />
        <RollFeed entries={feed} />
      </div>
    </>
  )
}
