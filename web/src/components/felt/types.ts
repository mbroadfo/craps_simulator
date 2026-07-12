/**
 * Dev-tool-local types for the felt port. Deliberately independent of
 * web/src/lib/tableReducer.ts — this step has no live data (see the
 * plan's Scope section); wiring these to TableState is Step 3.
 */
import type { RollType } from './data'

export interface CfgState {
  puck: number | null
  field2: 2 | 3
  field12: 2 | 3
  atsLit: Record<number, boolean>
}

export function defaultCfg(): CfgState {
  return {
    puck: null,
    field2: 2,
    field12: 3,
    atsLit: { 2: false, 3: false, 4: false, 5: false, 6: false, 8: false, 9: false, 10: false, 11: false, 12: false },
  }
}

// A bet zone on the felt: its anchor point (recorded once, at the
// moment a chip is first placed there) plus the stack of denomination
// values currently on it. Merges the prototype's separate `chips`/
// `chipAnchors` objects into one — every placeChip() call site already
// knows its own anchor from layout.ts at click time, so there's no
// need to record it as a side effect the way zone() used to.
export interface ChipZone {
  x: number
  y: number
  denoms: number[]
}

export interface RollRecord {
  shooter: number
  d1: number
  d2: number
  total: number
  type: RollType
}

export interface Toast {
  id: number
  amount: number
  x: number
  y: number
}
