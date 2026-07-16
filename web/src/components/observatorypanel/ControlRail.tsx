/**
 * The action bar — fixed in place (see .railControls in
 * ObservatoryPanel.css), always visible regardless of page scroll or
 * whether a table exists yet. Every button renders unconditionally,
 * in the same slot, at the same size, at all times — only :disabled
 * toggles. Nothing appears/disappears/reflows as the game starts;
 * before a table exists, Roll/Turbo/slider/Reset are simply greyed
 * out rather than absent.
 *
 * Start and Play/Pause are the same button — before a table exists it
 * reads "Start" (creates the table, but does NOT set it rolling: see
 * App.tsx's handleStart, which calls start() then immediately
 * pause()), and once one exists the identical ▶/⏸ slot becomes the
 * ordinary Play/Pause toggle. From there the game only ever
 * progresses via that toggle, Roll (single step, paused only), or
 * Turbo (jumps the speed slider to max).
 */
import type { TableSnapshot } from '../../lib/api'
import { useFeltState } from '../felt/state/FeltStateContext'
import './ObservatoryPanel.css'
import { DiceIcon, TurboIcon } from './RailIcons'

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

  const primaryTitle = !hasTable ? 'Start' : running ? 'Pause' : 'Play'
  const primaryDisabled = !hasTable ? creating || !canStart : finished
  const primaryClick = !hasTable ? onStart : onPauseResume

  return (
    <div className="railControls">
      <button className="railBtn" title="Toggle stats panel" aria-pressed={statsOpen} onClick={toggleStats}>
        ☰
      </button>
      {error && <div className="railError">{error}</div>}
      <button className="railBtn" title={primaryTitle} disabled={primaryDisabled} onClick={primaryClick}>
        {running ? '⏸' : '▶'}
      </button>
      <button className="railBtn" title="Roll — advance one roll, then stay paused" disabled={!paused} onClick={onStep}>
        <DiceIcon />
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
