/**
 * Adapts real TableState (web/src/lib/tableReducer.ts) + a parallel
 * roll log (liveRollLog.ts) into FeltUiState — the exact shape every
 * felt panel already reads via useFeltState() (Step 3, spectator
 * mode). No panel needed to change; this is the whole point of the
 * FeltUiState seam (see Felt.tsx's LiveFelt).
 *
 * Every write action (placeChip, rollDice, toggleAtsLit, ...) is a
 * no-op — there is no human bettor in spectator mode, so a click on a
 * live zone does nothing (see the plan's scope decision: manual play
 * is a separate future step with no backend support today).
 */
import { useCallback, useEffect, useRef, useState, type Dispatch, type SetStateAction } from 'react'
import { drainFadeUps, type ChipStack, type FadeUp, type PlayerState, type TableState } from '../../../lib/tableReducer'
import { chipDenomsForAmount, rackDenomsForAmount } from '../chips/chipDecompose'
import { stackedToastY } from '../toast/toastStack'
import { defaultCfg, type ChipZone, type FeltUiState, type RosterEntry, type Toast } from '../types'
import { feltZoneFor } from './feltZoneMap'
import type { RollLogState } from './liveRollLog'

let nextToastId = 0
const noop = () => {}

/** Bankroll minus the seat's starting bankroll, or null with no roll history yet. */
export function netFor(player: PlayerState | undefined): number | null {
  return player && player.history.length > 0 ? player.bankroll - player.history[0] : null
}

/**
 * Collapses this seat's ChipStacks into felt zones, carrying each
 * stack's working/not-working status through. Two ChipStacks (e.g. two
 * Come bets on the same number) can share a felt zone — if any part of
 * the pile is off, the whole zone reads as inactive, matching how a
 * dimmed stack looks on a real table.
 */
export function buildChipZones(chips: Map<string, ChipStack>, playerName: string): Record<string, ChipZone> {
  const zones: Record<string, ChipZone> = {}
  for (const stack of chips.values()) {
    if (stack.player !== playerName) continue
    const zone = feltZoneFor(stack.betType, stack.number)
    if (!zone) continue
    const total = stack.amounts.reduce((s, a) => s + a, 0)
    const denoms = chipDenomsForAmount(total)
    const existing = zones[zone.zoneId]
    const status = existing?.status === 'inactive' || stack.status === 'inactive' ? 'inactive' : stack.status
    zones[zone.zoneId] = existing
      ? { ...existing, denoms: [...existing.denoms, ...denoms], status }
      : { x: zone.x, y: zone.y, denoms, status }
  }
  return zones
}

/**
 * Groups this seat's fadeUps into one net toast per felt neighborhood
 * (Pass Line + Pass Line Odds; a Come bet and its odds on the same
 * number often resolve in the same roll — see the caller's own
 * comment for why they're merged instead of stacked). allReturn tracks
 * whether *every* resolution in a bucket was a refund: a returned odds
 * bet contributes exactly 0 to the sum, so a bucket that also contains
 * a real win or loss already nets to the true $ amount and should read
 * as that win/loss, not "Returned" — only a bucket built *entirely*
 * from returns gets the neutral treatment.
 */
export function buildToastBuckets(
  fadeUps: FadeUp[],
  playerName: string,
): Array<{ x: number; y: number; amount: number; kind: 'win' | 'loss' | 'return' }> {
  const buckets = new Map<string, { x: number; y: number; amount: number; allReturn: boolean }>()
  for (const f of fadeUps) {
    if (f.player !== playerName) continue
    const zone = feltZoneFor(f.betType, f.number)
    if (!zone) continue
    const key = `${Math.round(zone.x / 70)}_${Math.round(zone.y / 70)}`
    const isReturn = f.kind === 'return'
    const existing = buckets.get(key)
    if (existing) {
      existing.amount += f.delta
      existing.allReturn = existing.allReturn && isReturn
    } else {
      buckets.set(key, { x: zone.x, y: zone.y, amount: f.delta, allReturn: isReturn })
    }
  }
  return [...buckets.values()].map(({ x, y, amount, allReturn }) => ({
    x,
    y,
    amount,
    kind: allReturn ? 'return' : amount >= 0 ? 'win' : 'loss',
  }))
}

export function useFeltLiveState(
  tableState: TableState,
  rollLog: RollLogState,
  playerName: string,
  setPlayerName: Dispatch<SetStateAction<string>>,
  roster: RosterEntry[],
  setTableState: Dispatch<SetStateAction<TableState>>,
): FeltUiState {
  const [toasts, setToasts] = useState<Toast[]>([])
  const drainedThrough = useRef(-1)
  const [statsOpen, setStatsOpen] = useState(false)
  const toggleStats = useCallback(() => setStatsOpen((v) => !v), [])

  // Drain the *whole table's* fadeUps queue (all players) so it never
  // grows unbounded, but only turn this seat's own resolutions into a
  // visible toast.
  //
  // A single roll can resolve several of one player's bets in the
  // same felt neighborhood (Pass Line + Pass Line Odds; a Come bet and
  // its odds on the same number) — an active strategy does this
  // routinely, and it'll only get more common as busier strategies
  // get watched here. Stacking N separate toast boxes for that never
  // scales: past 2-3 they visually merge into noise and start
  // climbing high enough to cover the puck/box numbers. Instead,
  // resolutions that land in the same neighborhood on the same roll
  // are combined into one toast showing their net effect — the
  // number of toasts tracks how many distinct areas of the felt were
  // touched this roll, not how many individual bets resolved.
  useEffect(() => {
    const fresh = tableState.fadeUps.filter((f) => f.seq > drainedThrough.current)
    if (fresh.length === 0) return
    const maxSeq = Math.max(drainedThrough.current, ...fresh.map((f) => f.seq))
    for (const { x, y, amount, kind } of buildToastBuckets(fresh, playerName)) {
      const id = nextToastId++
      setToasts((prev) => [...prev, { id, amount, kind, x, y: stackedToastY(prev, x, y - 50) }])
      setTimeout(() => setToasts((prev) => prev.filter((t) => t.id !== id)), 1500)
    }
    drainedThrough.current = maxSeq
    setTableState((s) => drainFadeUps(s, maxSeq))
  }, [tableState.fadeUps, playerName, setTableState])

  const chips = buildChipZones(tableState.chips, playerName)

  // rack has no real "unplaced inventory" concept for a bot — the
  // chip rail is visible in live mode, though (Mike wants to watch it
  // shrink/grow), so it's decomposed into a textured pile that tracks
  // bankroll. rackDenomsForAmount (not the plain greedy
  // chipDenomsForAmount bet stacks use) specifically because a bare
  // greedy breakdown collapses a few-hundred-dollar bankroll into
  // essentially one $500+$100 chip, which barely visibly changes for
  // a typical $10-$50 win — unlike a bet stack, the rack has no
  // dollar label at all, so chip texture is the only signal it has.
  const feltTotal = Object.values(chips).reduce((sum, z) => sum + z.denoms.reduce((s, d) => s + d, 0), 0)
  const player = tableState.players.get(playerName)
  const bankroll = player?.bankroll ?? 0
  const rack: Record<number, number> = {}
  for (const d of rackDenomsForAmount(Math.max(0, bankroll - feltTotal))) rack[d] = (rack[d] ?? 0) + 1
  const net = netFor(player)

  const atsLit = defaultCfg().atsLit
  for (const r of rollLog.rolls) {
    if (r.shooter === tableState.shooterIndex) atsLit[r.total] = true
  }

  return {
    cfg: { puck: tableState.point, field2: 2, field12: 3, atsLit },
    setCfg: noop,
    rack,
    chips,
    // No real denomination selection in live mode (no picker to
    // select from) — a value no real DENOMS entry matches, so
    // ChipRail's "selected" gold-dot indicator never renders.
    selectedDenom: -1,
    setSelectedDenom: noop,
    hoverInfo: '',
    setHoverInfo: noop,
    placeChip: noop,
    removeChip: noop,
    clearAllBets: noop,
    toggleAtsLit: noop,
    toggleAtsSet: noop,
    setField2: noop,
    setField12: noop,
    setPuck: noop,
    rollHistory: rollLog.rolls,
    shooterNum: tableState.shooterIndex,
    shooterName: tableState.shooterName,
    net,
    roster,
    selectedPlayer: playerName,
    setSelectedPlayer: setPlayerName,
    rollDice: noop,
    resetShooter: noop,
    toasts,
    pushToast: noop,
    testAllBets: noop,
    exportJson: noop,
    statsOpen,
    toggleStats,
  }
}
