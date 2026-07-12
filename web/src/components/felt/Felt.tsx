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
import { FeltStateProvider } from './state/FeltStateContext'
import { BetToast } from './toast/BetToast'
import { FELT_H_BG, FELT_VIEWBOX, FELT_W } from './layout'

/**
 * Faithful port of prototype/parametric-felt.html — Step 2, complete.
 * Every visual piece is in: felt interior, chip rail, action bar,
 * dev-controls panel, shooter history, win/loss toasts, and the stats
 * sidebar (left of the table, matching the prototype's own layout
 * decision).
 *
 * JSX ordering inside <svg> intentionally mirrors the prototype's own
 * render() DOM order — do not reorder groups here without checking
 * that order still matches (see the plan's Risk #3: z-ordering is an
 * implicit contract, not enforced by anything else).
 */
export function Felt() {
  return (
    <FeltStateProvider>
      <FeltInner />
    </FeltStateProvider>
  )
}

function FeltInner() {
  return (
    <div className="pit-felt-root">
      <DevControlsPanel />
      <div className="pageRow">
        <StatsSidebar />
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

            <g id="chip-rail">
              <ChipRail />
            </g>

            {/* win/loss toasts — always last so they render on top of everything else */}
            <BetToast />
          </svg>

          <ActionBar />
        </div>

        <ShooterHistory />
      </div>
    </div>
  )
}
