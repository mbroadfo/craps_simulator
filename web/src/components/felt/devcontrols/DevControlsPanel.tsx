import { useState } from 'react'
import { SMALL_NUMS, TALL_NUMS } from '../layout'
import { useFeltState } from '../state/FeltStateContext'

const PUCK_VALUES = [4, 5, 6, 8, 9, 10]

/**
 * Hamburger menu + dev-controls panel — puck/field2/field12 direct
 * setters, ATS demo buttons, win/loss toast test, export. Shooter
 * roll/reset lives in the main action bar now (Roll is already there;
 * Reset is behind the "…" expand button next to it) — no need for a
 * second copy here. The old Sections/Table on-off toggle groups were
 * dropped entirely: they never had real off-state rendering wired
 * into the panels, so the buttons did nothing (Mike's call — not
 * worth building out for this prototype).
 */
export function DevControlsPanel() {
  const [open, setOpen] = useState(false)
  const { cfg, setPuck, setField2, setField12, toggleAtsSet, testAllBets, exportJson, hoverInfo } = useFeltState()
  const atsSets: [string, string, number[]][] = [
    ['ALL', 'aAll', [...SMALL_NUMS, ...TALL_NUMS]],
    ['TALL', 'aTall', TALL_NUMS],
    ['SMALL', 'aSmall', SMALL_NUMS],
  ]

  return (
    <>
      <button id="menuToggle" aria-label="Toggle dev controls" onClick={() => setOpen((v) => !v)}>
        &#9776;
      </button>
      <div className={'controls' + (open ? ' open' : '')} id="controlsPanel">
        <div className="grp">
          <label>Puck</label>
          <button className={cfg.puck === null ? 'on' : ''} onClick={() => setPuck(null)}>
            OFF
          </button>
          {PUCK_VALUES.map((v) => (
            <button key={v} className={cfg.puck === v ? 'on' : ''} onClick={() => setPuck(v)}>
              {v}
            </button>
          ))}
        </div>
        <div className="grp">
          <label>Field 2</label>
          <button onClick={setField2}>{cfg.field2}&times;</button>
        </div>
        <div className="grp">
          <label>Field 12</label>
          <button onClick={setField12}>{cfg.field12}&times;</button>
        </div>
        <div className="grp">
          <label>ATS demo</label>
          {atsSets.map(([label, id, nums]) => (
            <button key={id} onClick={() => toggleAtsSet(nums)}>
              {label}
            </button>
          ))}
        </div>
        <div className="grp">
          <label>Win/Loss test</label>
          <button onClick={() => testAllBets(1)}>+$10</button>
          <button onClick={() => testAllBets(-1)}>&minus;$10</button>
        </div>
        <div className="grp">
          <label>Data</label>
          <button onClick={exportJson}>EXPORT JSON</button>
        </div>
        <div id="readout">{hoverInfo}</div>
      </div>
    </>
  )
}
