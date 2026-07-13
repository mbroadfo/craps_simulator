import type { TableSnapshot } from '../../../lib/api'

/**
 * Live-mode sibling of ActionBar (which stays dev-only: Roll/Clear/
 * Reset + DenomPicker, none of which mean anything for a bot table).
 * Same slot, same .iconBtn visual language, but pause/resume/turbo —
 * session-lifecycle actions that live in App.tsx (it owns the
 * TableSnapshot/api calls), passed down as plain callbacks rather
 * than threaded through FeltUiState, which has no concept of a
 * session at all.
 */
export function LiveActionBar({
  sessionState,
  onPauseResume,
  onTurbo,
  turboOn,
  onStep,
}: {
  sessionState: TableSnapshot['state'] | null
  onPauseResume: () => void
  onTurbo: () => void
  turboOn: boolean
  onStep: () => void
}) {
  const disabled = sessionState === null || sessionState === 'finished' || sessionState === 'stopped'
  const paused = sessionState === 'paused'

  return (
    <div className="actionBar">
      <div className="btnRow">
        <button className="iconBtn" title={paused ? 'Resume' : 'Pause'} disabled={disabled} onClick={onPauseResume}>
          {paused ? '▶' : '⏸'}
        </button>
        {/* Only meaningful while paused — advances exactly one roll
            then re-pauses (table_session.py's step()), for watching a
            suspicious sequence roll-by-roll instead of at full pace. */}
        <button className="iconBtn" title="Step — advance one roll, then stay paused" disabled={!paused} onClick={onStep}>
          {'⏭'}
        </button>
        <button className={'iconBtn' + (turboOn ? ' primary' : '')} title="Turbo — no roll delay" disabled={disabled} onClick={onTurbo}>
          {'⏩'}
        </button>
      </div>
    </div>
  )
}
