/**
 * The wire vocabulary (Phase 2, D3): TypeScript mirror of the frozen
 * dataclasses in craps/events.py. Field names match the Python event
 * fields exactly — the Python vocabulary IS the wire schema. Every
 * envelope is `{seq, table_id, type, ...payload}`.
 *
 * JSON has no tuples, so tuple-shaped Python fields arrive as arrays:
 * dice pairs, per-player pair lists, and hop-bet numbers like [3, 3].
 */

/** int | hop pair | not-yet-numbered */
export type BetNumber = number | [number, number] | null

interface Base {
  seq: number
  table_id: string
}

export interface SessionStarted extends Base {
  type: 'SessionStarted'
  num_shooters: number
}

export interface ShooterAssigned extends Base {
  type: 'ShooterAssigned'
  shooter_index: number
  shooter_name: string
}

export interface BetsRequested extends Base {
  type: 'BetsRequested'
}

export interface BetPlaced extends Base {
  type: 'BetPlaced'
  player_name: string
  bet_type: string
  amount: number
  number: BetNumber
}

export interface BetMoved extends Base {
  type: 'BetMoved'
  player_name: string
  bet_type: string
  amount: number
  number: number
}

export interface BetAdjusted extends Base {
  type: 'BetAdjusted'
  player_name: string
  bet_type: string
  amount: number
  number: BetNumber
  status: string
}

export interface BetStatusChanged extends Base {
  type: 'BetStatusChanged'
  player_name: string
  bet_type: string
  number: BetNumber
  status: string
}

export interface DiceRolled extends Base {
  type: 'DiceRolled'
  shooter_index: number
  roll_number: number
  dice: [number, number]
  total: number
  phase: 'come-out' | 'point'
  point: number | null
  table_risk: number
  shooter_name: string
}

export interface BetResolved extends Base {
  type: 'BetResolved'
  player_name: string
  bet_type: string
  amount: number
  number: BetNumber
  status: string
  payout: number
  win_payout: number
  /** Whether settlement took the chip off the table ("if it pays, it
   * stays" winners keep their felt position). */
  removed: boolean
}

export interface NumberHit extends Base {
  type: 'NumberHit'
  total: number
  message: string
}

export interface GameStateChanged extends Base {
  type: 'GameStateChanged'
  message: string
}

export interface BankrollsUpdated extends Base {
  type: 'BankrollsUpdated'
  bankrolls: [string, number][]
}

export interface RiskUpdated extends Base {
  type: 'RiskUpdated'
  at_risk: [string, number][]
}

export interface PointEstablished extends Base {
  type: 'PointEstablished'
  point: number
}

export interface PointHit extends Base {
  type: 'PointHit'
  point: number
}

export interface SevenOut extends Base {
  type: 'SevenOut'
  shooter_index: number
  shooter_results: [string, number][]
}

export interface SessionFinalized extends Base {
  type: 'SessionFinalized'
  session_rolls: number
}

export type Envelope =
  | SessionStarted
  | ShooterAssigned
  | BetsRequested
  | BetPlaced
  | BetMoved
  | BetAdjusted
  | BetStatusChanged
  | DiceRolled
  | BetResolved
  | NumberHit
  | GameStateChanged
  | BankrollsUpdated
  | RiskUpdated
  | PointEstablished
  | PointHit
  | SevenOut
  | SessionFinalized

export const EVENT_TYPES = [
  'SessionStarted',
  'ShooterAssigned',
  'BetsRequested',
  'BetPlaced',
  'BetMoved',
  'BetAdjusted',
  'BetStatusChanged',
  'DiceRolled',
  'BetResolved',
  'NumberHit',
  'GameStateChanged',
  'BankrollsUpdated',
  'RiskUpdated',
  'PointEstablished',
  'PointHit',
  'SevenOut',
  'SessionFinalized',
] as const satisfies readonly Envelope['type'][]
