/**
 * The event stream → render state (Phase 2, Step 2 core).
 *
 * A pure reducer: whatever the felt looks like, it renders this state.
 * Chip semantics mirror tests/test_bet_events.py's ChipTracker exactly
 * (the Python twin, proven orphan-free against the engine):
 *
 * - Chips are a MULTISET keyed (player, bet_type, number) — stacks of
 *   amounts. Two Come bets can legitimately occupy the same number.
 * - Events referencing a numbered chip fall back to the un-numbered
 *   stack when the exact key misses (number filled at resolution:
 *   odds settled the same roll they attached, the Field win-number
 *   quirk).
 * - BetResolved removes a chip only when `removed` says settlement
 *   took it down — winners can stay up.
 *
 * Orphan events (chips the stream never placed) are collected, not
 * thrown: in production they indicate a bug worth logging; in the
 * fixture test they fail the build.
 */
import type { BetNumber, Envelope } from './events'

export interface ChipStack {
  player: string
  betType: string
  number: BetNumber
  /** one entry per bet instance on this position */
  amounts: number[]
  /** last known working status for the position */
  status: string
}

export interface FadeUp {
  seq: number
  player: string
  betType: string
  number: BetNumber
  /** signed display amount: +winnings or -stake */
  delta: number
  win: boolean
}

export interface PlayerState {
  bankroll: number
  history: number[]
  atRisk: number
}

export interface TableState {
  tableId: string | null
  numShooters: number
  shooterIndex: number
  shooterName: string
  phase: 'come-out' | 'point'
  point: number | null
  puckOn: boolean
  dice: [number, number] | null
  rollNumber: number
  chips: Map<string, ChipStack>
  players: Map<string, PlayerState>
  /** BetResolved animations; the view drains what it has shown */
  fadeUps: FadeUp[]
  finished: boolean
  orphans: Envelope[]
}

export function initialState(): TableState {
  return {
    tableId: null,
    numShooters: 0,
    shooterIndex: 0,
    shooterName: '',
    phase: 'come-out',
    point: null,
    puckOn: false,
    dice: null,
    rollNumber: 0,
    chips: new Map(),
    players: new Map(),
    fadeUps: [],
    finished: false,
    orphans: [],
  }
}

const chipKey = (player: string, betType: string, number: BetNumber) =>
  `${player}|${betType}|${JSON.stringify(number)}`

/** Exact key, else the un-numbered fallback (see module docstring). */
function findStack(
  chips: Map<string, ChipStack>,
  player: string,
  betType: string,
  number: BetNumber,
): string | null {
  const exact = chipKey(player, betType, number)
  if (chips.get(exact)?.amounts.length) return exact
  const fallback = chipKey(player, betType, null)
  if (chips.get(fallback)?.amounts.length) return fallback
  return null
}

function pushChip(
  chips: Map<string, ChipStack>,
  player: string,
  betType: string,
  number: BetNumber,
  amount: number,
): void {
  const key = chipKey(player, betType, number)
  const stack = chips.get(key)
  if (stack) {
    chips.set(key, { ...stack, amounts: [...stack.amounts, amount] })
  } else {
    chips.set(key, { player, betType, number, amounts: [amount], status: 'active' })
  }
}

/** Remove one instance, matching by amount when possible. */
function popChip(chips: Map<string, ChipStack>, key: string, amount: number): void {
  const stack = chips.get(key)
  if (!stack) return
  const amounts = [...stack.amounts]
  const i = amounts.indexOf(amount)
  amounts.splice(i >= 0 ? i : amounts.length - 1, 1)
  if (amounts.length === 0) chips.delete(key)
  else chips.set(key, { ...stack, amounts })
}

function getPlayer(players: Map<string, PlayerState>, name: string): PlayerState {
  return players.get(name) ?? { bankroll: 0, history: [], atRisk: 0 }
}

const SPARKLINE_POINTS = 120

export function tableReducer(state: TableState, e: Envelope): TableState {
  switch (e.type) {
    case 'SessionStarted':
      return { ...state, tableId: e.table_id, numShooters: e.num_shooters }

    case 'ShooterAssigned':
      return { ...state, shooterIndex: e.shooter_index, shooterName: e.shooter_name }

    case 'DiceRolled':
      return {
        ...state,
        dice: e.dice,
        rollNumber: e.roll_number,
        phase: e.phase,
        point: e.point,
        puckOn: e.phase === 'point',
        shooterName: e.shooter_name,
      }

    case 'PointEstablished':
      return { ...state, phase: 'point', point: e.point, puckOn: true }

    case 'PointHit':
    case 'SevenOut':
      return { ...state, phase: 'come-out', point: null, puckOn: false }

    case 'BetPlaced': {
      const chips = new Map(state.chips)
      pushChip(chips, e.player_name, e.bet_type, e.number, e.amount)
      return { ...state, chips }
    }

    case 'BetMoved': {
      const source = findStack(state.chips, e.player_name, e.bet_type, null)
      if (source === null) return { ...state, orphans: [...state.orphans, e] }
      const chips = new Map(state.chips)
      popChip(chips, source, e.amount)
      pushChip(chips, e.player_name, e.bet_type, e.number, e.amount)
      return { ...state, chips }
    }

    case 'BetAdjusted': {
      const key = findStack(state.chips, e.player_name, e.bet_type, e.number)
      if (key === null) return { ...state, orphans: [...state.orphans, e] }
      const chips = new Map(state.chips)
      const stack = chips.get(key)!
      const amounts = [...stack.amounts]
      amounts[amounts.length - 1] = e.amount
      chips.set(key, { ...stack, amounts, status: e.status })
      return { ...state, chips }
    }

    case 'BetStatusChanged': {
      const key = findStack(state.chips, e.player_name, e.bet_type, e.number)
      if (key === null) return { ...state, orphans: [...state.orphans, e] }
      const chips = new Map(state.chips)
      chips.set(key, { ...chips.get(key)!, status: e.status })
      return { ...state, chips }
    }

    case 'BetResolved': {
      const key = findStack(state.chips, e.player_name, e.bet_type, e.number)
      if (key === null) return { ...state, orphans: [...state.orphans, e] }
      const chips = new Map(state.chips)
      if (e.removed) popChip(chips, key, e.amount)
      const win = e.status === 'won'
      const fadeUp: FadeUp = {
        seq: e.seq,
        player: e.player_name,
        betType: e.bet_type,
        number: e.number,
        delta: win ? e.payout : -e.amount,
        win,
      }
      return { ...state, chips, fadeUps: [...state.fadeUps, fadeUp] }
    }

    case 'BankrollsUpdated': {
      const players = new Map(state.players)
      for (const [name, balance] of e.bankrolls) {
        const p = getPlayer(players, name)
        players.set(name, {
          ...p,
          bankroll: balance,
          history: [...p.history.slice(-(SPARKLINE_POINTS - 1)), balance],
        })
      }
      return { ...state, players }
    }

    case 'RiskUpdated': {
      const players = new Map(state.players)
      for (const [name, atRisk] of e.at_risk) {
        players.set(name, { ...getPlayer(players, name), atRisk })
      }
      return { ...state, players }
    }

    case 'SessionFinalized':
      return { ...state, finished: true }

    case 'BetsRequested':
    case 'NumberHit':
    case 'GameStateChanged':
      return state
  }
}

/** The view calls this after rendering the animations it consumed. */
export function drainFadeUps(state: TableState, shownThroughSeq: number): TableState {
  const fadeUps = state.fadeUps.filter((f) => f.seq > shownThroughSeq)
  return fadeUps.length === state.fadeUps.length ? state : { ...state, fadeUps }
}
