/**
 * Dev-tool-local types for the felt port, deliberately independent of
 * web/src/lib/tableReducer.ts's wire types — bet placement here is a
 * felt-local zone id, not a (player, betType, number) key. FeltUiState
 * is the shared contract both useFeltDevState (dev mode) and
 * useFeltLiveState (Step 3 spectator mode) return, so every panel
 * component can read via useFeltState() without caring which one is
 * behind it.
 */
import type { Dispatch, SetStateAction } from 'react'
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

/** A seated player, for the sidebar's Current-section perspective dropdown. */
export interface RosterEntry {
  name: string
  strategy: string
}

export interface FeltUiState {
  cfg: CfgState
  setCfg: Dispatch<SetStateAction<CfgState>>
  rack: Record<number, number>
  chips: Record<string, ChipZone>
  selectedDenom: number
  setSelectedDenom: Dispatch<SetStateAction<number>>
  hoverInfo: string
  setHoverInfo: Dispatch<SetStateAction<string>>
  placeChip: (zoneId: string, x: number, y: number, denom: number) => void
  removeChip: (zoneId: string) => void
  clearAllBets: () => void
  toggleAtsLit: (n: number) => void
  toggleAtsSet: (nums: number[]) => void
  setField2: () => void
  setField12: () => void
  setPuck: (value: number | null) => void
  rollHistory: RollRecord[]
  shooterNum: number
  shooterName: string
  /** Net win/loss for the displayed seat, or null with no real source (dev mode). */
  net: number | null
  /** Seated players (live mode) — empty in dev mode, so the sidebar's
   * Current-section dropdown falls back to a plain label there. */
  roster: RosterEntry[]
  selectedPlayer: string
  setSelectedPlayer: (name: string) => void
  rollDice: () => void
  resetShooter: () => void
  toasts: Toast[]
  pushToast: (amount: number, x: number, y: number) => void
  testAllBets: (sign: 1 | -1) => void
  exportJson: () => void
  /** The stats sidebar overlay's open/closed state — lives here (not
   * local state in Felt.tsx) so ControlRail, rendered outside the felt
   * proper in the Observatory panel, can toggle it via useFeltState()
   * without prop-drilling through App.tsx. */
  statsOpen: boolean
  toggleStats: () => void
}
