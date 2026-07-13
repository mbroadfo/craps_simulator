import { useCallback, useState } from 'react'
import { classifyRoll, startingRack } from '../data'
import { stackedToastY } from '../toast/toastStack'
import { defaultCfg, type CfgState, type ChipZone, type FeltUiState, type RollRecord, type Toast } from '../types'

let nextToastId = 0
const noop = () => {}

/**
 * The dev-tool state the prototype kept as module-level mutable
 * globals (cfg, rack, chips/chipAnchors, selectedDenom, rollHistory/
 * shooterNum, toasts) — now real React state, owned by one hook and
 * shared via FeltStateContext. Return shape is FeltUiState — the same
 * contract useFeltLiveState (Step 3 spectator mode) conforms to.
 */
export function useFeltDevState(): FeltUiState {
  const [cfg, setCfg] = useState<CfgState>(defaultCfg)
  // rack and chips update together (spend on place, credit on remove) —
  // one state object so the check-then-mutate is atomic within a
  // single setState updater, matching the prototype's synchronous
  // rack[selectedDenom] -= 1; chips[chipId].push(...) pairing.
  const [rackChips, setRackChips] = useState<{ rack: Record<number, number>; chips: Record<string, ChipZone> }>(() => ({
    rack: startingRack(),
    chips: {},
  }))
  const [selectedDenom, setSelectedDenom] = useState(25)
  const [hoverInfo, setHoverInfo] = useState('hover a zone…')
  const [rollHistory, setRollHistory] = useState<RollRecord[]>([])
  const [shooterNum, setShooterNum] = useState(1)
  // True right after a seven-out is logged — the NEXT roll is the one
  // that actually belongs to the new shooter, so the bump is delayed
  // one roll (see rollDice's own comment: bumping shooterNum in the
  // same call that logs the seven-out made the shooter-filtered
  // ShooterHistory view exclude that roll on the very render it
  // appeared in — the red 7 never showed).
  const [pendingNewShooter, setPendingNewShooter] = useState(false)
  const [toasts, setToasts] = useState<Toast[]>([])

  const placeChip = useCallback((zoneId: string, x: number, y: number, denom: number) => {
    setRackChips((prev) => {
      if (!prev.rack[denom]) return prev
      const nextRack = { ...prev.rack, [denom]: prev.rack[denom] - 1 }
      const existing = prev.chips[zoneId]
      const nextZone: ChipZone = existing ? { ...existing, denoms: [...existing.denoms, denom] } : { x, y, denoms: [denom] }
      return { rack: nextRack, chips: { ...prev.chips, [zoneId]: nextZone } }
    })
  }, [])

  const removeChip = useCallback((zoneId: string) => {
    setRackChips((prev) => {
      const zone = prev.chips[zoneId]
      if (!zone || zone.denoms.length === 0) return prev
      const denom = zone.denoms[zone.denoms.length - 1]
      const restDenoms = zone.denoms.slice(0, -1)
      const nextChips = { ...prev.chips }
      if (restDenoms.length === 0) delete nextChips[zoneId]
      else nextChips[zoneId] = { ...zone, denoms: restDenoms }
      const nextRack = { ...prev.rack, [denom]: (prev.rack[denom] || 0) + 1 }
      return { rack: nextRack, chips: nextChips }
    })
  }, [])

  const clearAllBets = useCallback(() => {
    // Clear returns the felt's chips to the rack — a bet pulled before
    // the roll goes back in the player's hand, it doesn't vanish.
    setRackChips((prev) => {
      const nextRack = { ...prev.rack }
      for (const zone of Object.values(prev.chips)) {
        for (const denom of zone.denoms) nextRack[denom] = (nextRack[denom] || 0) + 1
      }
      return { rack: nextRack, chips: {} }
    })
  }, [])

  const toggleAtsLit = useCallback((n: number) => {
    setCfg((prev) => ({ ...prev, atsLit: { ...prev.atsLit, [n]: !prev.atsLit[n] } }))
  }, [])

  // ATS demo buttons light number SETS: toggles the whole group on/off.
  const toggleAtsSet = useCallback((nums: number[]) => {
    setCfg((prev) => {
      const allLit = nums.every((n) => prev.atsLit[n])
      const nextLit = { ...prev.atsLit }
      for (const n of nums) nextLit[n] = !allLit
      return { ...prev, atsLit: nextLit }
    })
  }, [])

  const setField2 = useCallback(() => {
    setCfg((prev) => ({ ...prev, field2: prev.field2 === 2 ? 3 : 2 }))
  }, [])
  const setField12 = useCallback(() => {
    setCfg((prev) => ({ ...prev, field12: prev.field12 === 3 ? 2 : 3 }))
  }, [])

  const setPuck = useCallback((value: number | null) => {
    setCfg((prev) => ({ ...prev, puck: value }))
  }, [])

  // A genuine random 2d6 roller (no bet-resolution/payout logic — out
  // of scope for this prototype) that tracks point/seven-out state and
  // colors each roll via classifyRoll.
  //
  // Deliberately NOT nested setState-inside-setState (an earlier
  // version called setShooterNum/setRollHistory from inside setCfg's
  // updater) — StrictMode double-invokes updater functions to surface
  // impurity, and nesting them compounds that multiplicatively (2x
  // wrapping 2x = 4 rolls logged per click). Reading cfg.puck/
  // shooterNum from the closure (fresh every render via the deps
  // array) and firing independent, side-effect-free setState calls
  // avoids it.
  const rollDice = useCallback(() => {
    const d1 = 1 + Math.floor(Math.random() * 6)
    const d2 = 1 + Math.floor(Math.random() * 6)
    const total = d1 + d2
    const type = classifyRoll(d1, d2, cfg.puck)
    const nextPuck = type === 'seven-out' || type === 'point-hit' ? null : type === 'point-set' ? total : cfg.puck
    // This roll belongs to the new shooter only if the *previous* roll
    // was the seven-out that ended the last one — see pendingNewShooter.
    const activeShooter = pendingNewShooter ? shooterNum + 1 : shooterNum

    setCfg((prev) => ({ ...prev, puck: nextPuck }))
    setRollHistory((prev) => [...prev, { shooter: activeShooter, d1, d2, total, type }])
    if (pendingNewShooter) setShooterNum(activeShooter)
    setPendingNewShooter(type === 'seven-out')
  }, [cfg.puck, shooterNum, pendingNewShooter])

  const resetShooter = useCallback(() => {
    setRollHistory([])
    setShooterNum(1)
    setPendingNewShooter(false)
    setCfg((prev) => ({ ...prev, puck: null }))
  }, [])

  const pushToast = useCallback((amount: number, x: number, y: number) => {
    const id = nextToastId++
    setToasts((prev) => [...prev, { id, amount, x, y: stackedToastY(prev, x, y) }])
    setTimeout(() => setToasts((prev) => prev.filter((t) => t.id !== id)), 1500)
  }, [])

  // Manual triggers for the win/loss toast — one per currently active
  // bet (every zone with chips on it), each showing that bet's own
  // total, popping up just above its chip stack.
  const testAllBets = useCallback(
    (sign: 1 | -1) => {
      for (const zone of Object.values(rackChips.chips)) {
        if (!zone.denoms.length) continue
        const total = zone.denoms.reduce((sum, v) => sum + v, 0)
        pushToast(sign * total, zone.x, zone.y - 50)
      }
    },
    [rackChips.chips, pushToast],
  )

  const exportJson = useCallback(() => {
    const wager = Object.values(rackChips.chips).reduce((sum, zone) => sum + zone.denoms.reduce((s, d) => s + d, 0), 0)
    const data = JSON.stringify({ chips: rackChips.chips, rack: rackChips.rack, wager }, null, 2)
    const blob = new Blob([data], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'felt-bets.json'
    a.click()
    URL.revokeObjectURL(url)
  }, [rackChips])

  return {
    cfg,
    setCfg,
    rack: rackChips.rack,
    chips: rackChips.chips,
    selectedDenom,
    setSelectedDenom,
    hoverInfo,
    setHoverInfo,
    placeChip,
    removeChip,
    clearAllBets,
    toggleAtsLit,
    toggleAtsSet,
    setField2,
    setField12,
    setPuck,
    rollHistory,
    shooterNum,
    shooterName: `Shooter ${shooterNum}`,
    net: null,
    roster: [],
    selectedPlayer: '',
    setSelectedPlayer: noop,
    rollDice,
    resetShooter,
    toasts,
    pushToast,
    testAllBets,
    exportJson,
  }
}
