/**
 * The action bar — fixed in place (see .railControls in
 * ObservatoryPanel.css), always visible regardless of page scroll or
 * whether a table exists yet. Every button renders unconditionally,
 * in the same slot, at the same size, at all times — only :disabled
 * toggles. Nothing appears/disappears/reflows as the game starts;
 * before a table exists, Autoplay/Turbo/slider/Reset are simply
 * greyed out rather than absent.
 *
 * Start and Roll are the same button, same spot, same meaning
 * throughout: "advance by one." Before a table exists it reads
 * "Start" (creates the table, but does NOT set it rolling: see
 * App.tsx's handleStart, which calls start() then immediately
 * pause()); once one exists, the identical slot becomes Roll — a
 * single step, disabled while auto-rolling or finished. Continuous
 * rolling is a *separate* button (Autoplay, the Play/Pause toggle) so
 * "roll once" and "keep rolling" are never the same click target —
 * clicking Start twice in a row should never surprise you into
 * autoplay.
 */
import type { TableSnapshot } from '../../lib/api'
import { useFeltState } from '../felt/state/FeltStateContext'
import './ObservatoryPanel.css'
import { AutoplayIcon, DiceIcon, TurboIcon } from './RailIcons'

export const MAX_SPEED = 10

export function ControlRail({
  hasTable,
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
}: {
  hasTable: boolean
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
}) {
  const { statsOpen, toggleStats } = useFeltState()

  const running = sessionState === 'running'
  const paused = sessionState === 'paused'
  const finished = sessionState === 'finished' || sessionState === 'stopped'
  const turboActive = speed >= MAX_SPEED

  const primaryTitle = !hasTable ? 'Start' : 'Roll — advance one roll, then stay paused'
  const primaryDisabled = !hasTable ? creating || !canStart : !paused
  const primaryClick = !hasTable ? onStart : onStep

  const autoplayTitle = running ? 'Pause — stop auto-rolling' : 'Autoplay — roll continuously'
  const autoplayDisabled = !hasTable || finished

  return (
    <div className="railControls">
      <button className="railBtn" title="Toggle stats panel" aria-pressed={statsOpen} onClick={toggleStats}>
        ☰
      </button>
      {error && <div className="railError">{error}</div>}
      <button className="railBtn" title={primaryTitle} disabled={primaryDisabled} onClick={primaryClick}>
        {hasTable ? <DiceIcon /> : '▶'}
      </button>
      <button
        className={'railBtn' + (running ? ' active' : '')}
        title={autoplayTitle}
        disabled={autoplayDisabled}
        onClick={onPauseResume}
      >
        {running ? '⏸' : <AutoplayIcon />}
      </button>
      <button
        className={'railBtn' + (turboActive ? ' active' : '')}
        title="Turbo — jump to max speed"
        disabled={!hasTable || finished}
        onClick={() => onSpeedChange(turboActive ? 1 : MAX_SPEED)}
      >
        <TurboIcon />
      </button>
      <div className="railSliderWrap">
        <input
          className="railSlider"
          type="range"
          min={0.1}
          max={MAX_SPEED}
          step={0.1}
          value={speed}
          disabled={!hasTable}
          onChange={(e) => onSpeedChange(Number(e.target.value))}
        />
      </div>
      <span className={'railSpeedValue' + (turboActive ? ' turbo' : '')}>{turboActive ? 'TURBO' : `${speed.toFixed(1)}x`}</span>
      <button className="railBtn reset" title="Reset — end this game and start a new one" disabled={!hasTable} onClick={onReset}>
        ✕
      </button>
    </div>
  )
}
