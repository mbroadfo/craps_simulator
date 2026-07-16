import type { Dispatch, ReactNode, SetStateAction } from 'react'
import './Felt.css'
import { ActionBar } from './actionbar/ActionBar'
import { ChipRail } from './chips/ChipRail'
import { ChipStackLayer } from './chips/ChipStackLayer'
import { DevControlsPanel } from './devcontrols/DevControlsPanel'
import { ShooterHistory } from './history/ShooterHistory'
import { AtsPanel } from './panels/AtsPanel'
import { BoxNumbers } from './panels/BoxNumbers'
import { ComeBox } from './panels/ComeBox'
import { DontComeBox } from './panels/DontComeBox'
import { FieldBox } from './panels/FieldBox'
import { HopsPanel } from './panels/HopsPanel'
import { PropsPanel } from './panels/PropsPanel'
import { StatsSidebar } from './sidebar/StatsSidebar'
import { FeltDefs } from './shell/FeltDefs'
import { DpLabels, PassDontPassBands } from './shell/PassDontPassBands'
import { FeltStateProvider, useFeltState } from './state/FeltStateContext'
import { useFeltLiveState } from './state/useFeltLiveState'
import type { RollLogState } from './state/liveRollLog'
import type { RosterEntry } from './types'
import { BetToast } from './toast/BetToast'
import { FELT_H_BG, FELT_VIEWBOX, FELT_W } from './layout'
import type { TableState } from '../../lib/tableReducer'

/**
 * Faithful port of prototype/parametric-felt.html — Step 2, complete.
 * Every visual piece is in: felt interior, chip rail, action bar,
 * dev-controls panel, shooter history, win/loss toasts, and the stats
 * sidebar — a hamburger-triggered left overlay rather than a permanent
 * .pageRow column, so the felt and right panel can use its width.
 *
 * JSX ordering inside <svg> intentionally mirrors the prototype's own
 * render() DOM order — do not reorder groups here without checking
 * that order still matches (see the plan's Risk #3: z-ordering is an
 * implicit contract, not enforced by anything else).
 */
export function Felt() {
  return (
    <FeltStateProvider>
      <FeltInner mode="dev" />
    </FeltStateProvider>
  )
}

/**
 * Step 3, spectator mode: same felt, fed by a pre-built FeltUiState
 * (useFeltLiveState) instead of the dev-tool hook. Click-to-place and
 * the dev-controls panel only make sense for a human bettor — neither
 * exists in live mode. The chip rail stays, showing the selected
 * seat's real bankroll (decomposed, shrinks/grows with it).
 *
 * Session-lifecycle controls (Play/Roll/Turbo/Reset) and the lineup
 * builder live in ObservatoryPanel/ControlRail now, both rendered
 * inside the Observatory panel itself (ControlRail sits to the right
 * of the current-roll/bot-roster column) — the felt itself knows
 * nothing about session lifecycle in live mode at all.
 */
export function LiveFelt({
  tableState,
  rollLog,
  playerName,
  setPlayerName,
  roster,
  setTableState,
  sidebar,
}: {
  tableState: TableState
  rollLog: RollLogState
  playerName: string
  setPlayerName: Dispatch<SetStateAction<string>>
  roster: RosterEntry[]
  setTableState: Dispatch<SetStateAction<TableState>>
  sidebar?: ReactNode
}) {
  const state = useFeltLiveState(tableState, rollLog, playerName, setPlayerName, roster, setTableState)
  return (
    <FeltStateProvider value={state}>
      <FeltInner mode="live" sidebar={sidebar} />
    </FeltStateProvider>
  )
}

function FeltInner({ mode, sidebar }: { mode: 'dev' | 'live'; sidebar?: ReactNode }) {
  // statsOpen/toggleStats live in FeltUiState (not local state here) so
  // ControlRail, rendered outside the felt proper in the Observatory
  // panel, can toggle the overlay via useFeltState() too — see the
  // hamburger button now living at the top of the action bar.
  const { statsOpen, toggleStats } = useFeltState()

  return (
    <div className="pit-felt-root">
      {mode === 'dev' && <DevControlsPanel />}

      {/* Stats sidebar is an overlay, not a permanent .pageRow column.
          Overlay panel itself is always mounted (never conditionally
          unrendered) so the slide transform has something to animate
          and Felt.test.tsx's stats-section queries keep working
          regardless of open state. */}
      {statsOpen && <div className="statsOverlayBackdrop" onClick={toggleStats} />}
      <div className={'statsOverlay' + (statsOpen ? ' open' : '')}>
        <StatsSidebar />
      </div>

      <div className="pageRow">
        <div className="tableWrap">
          <svg
            id="felt"
            viewBox={FELT_VIEWBOX}
            xmlns="http://www.w3.org/2000/svg"
            aria-label="Craps table — The Pit"
          >
            <FeltDefs />

            {/* Extends a bit past the printed betting area (y=724) down
                to y=743 — table apron, not printed felt — so the gap
                before the chip rail reads as part of the table instead
                of empty page background. */}
            <rect width={FELT_W} height={FELT_H_BG} rx={16} fill="url(#felt-bg)" />

            <PassDontPassBands />

            {/* rail on top so band fills tuck under it cleanly */}
            <rect width={FELT_W} height={FELT_H_BG} rx={16} fill="none" stroke="#4a3a1d" strokeWidth={6} />
            <rect x={3} y={3} width={1394} height={737} rx={14} fill="none" stroke="#a07030" strokeWidth={1} strokeOpacity={0.5} />

            <g id="dp-labels">
              <DpLabels />
            </g>

            {/* interior — order mirrors the prototype's render(): ATS,
                Hops, Props, then Box Numbers, Don't Come, Come, Field.
                Do not reorder. */}
            <g id="interior">
              <AtsPanel />
              <HopsPanel />
              <PropsPanel />
              <BoxNumbers />
              <DontComeBox />
              <ComeBox />
              <FieldBox />
              {/* bets placed on the felt render last within interior, on
                  top of the panels, matching drawChipLayer() in the
                  prototype (its own <g>, appended after all draw*() calls) */}
              <ChipStackLayer />
            </g>

            {/* Chip rail — visible in both modes. Live mode shows the
                selected seat's real bankroll, decomposed into a
                textured pile (see useFeltLiveState's rack); clicking
                it is still a harmless no-op (no denom picker to feed
                in live mode). */}
            <g id="chip-rail">
              <ChipRail />
            </g>

            {/* win/loss toasts — always last so they render on top of everything else */}
            <BetToast />
          </svg>

          {mode === 'dev' && <ActionBar />}
        </div>

        <ShooterHistory />
        {sidebar}
      </div>
    </div>
  )
}
