import { describe, expect, it } from 'vitest'
import type { DiceRolled, Envelope, SessionStarted } from '../../../lib/events'
import { initialRollLogState, rollLogReducer } from './liveRollLog'

let seq = 0
// phase/point describe the state BEFORE this roll (see roll_dice() in
// table_runner.py — it publishes off game_state.phase/point strictly
// before resolve_bets() updates them), matching engine reality.
function mkRoll(overrides: Partial<DiceRolled>): DiceRolled {
  const dice = overrides.dice ?? [3, 4]
  return {
    type: 'DiceRolled',
    seq: seq++,
    table_id: 't1',
    shooter_index: 0,
    roll_number: seq,
    dice,
    total: dice[0] + dice[1],
    phase: 'come-out',
    point: null,
    table_risk: 0,
    shooter_name: 'Molly',
    ...overrides,
  }
}

describe('rollLogReducer', () => {
  it('starts empty', () => {
    expect(initialRollLogState().rolls).toEqual([])
  })

  it('classifies a come-out roll that sets the point (no point was on before it)', () => {
    const roll = mkRoll({ dice: [2, 4], phase: 'come-out', point: null })
    const state = rollLogReducer(initialRollLogState(), roll)
    expect(state.rolls).toEqual([{ shooter: 0, d1: 2, d2: 4, total: 6, type: 'point-set' }])
  })

  it('classifies the point being hit — point was already on before this roll', () => {
    const roll = mkRoll({ dice: [1, 5], phase: 'point', point: 6 })
    const state = rollLogReducer(initialRollLogState(), roll)
    expect(state.rolls[0].type).toBe('point-hit')
  })

  it('classifies a seven-out — point was on before this roll and it sevened', () => {
    const roll = mkRoll({ dice: [3, 4], phase: 'point', point: 8 })
    const state = rollLogReducer(initialRollLogState(), roll)
    expect(state.rolls[0].type).toBe('seven-out')
  })

  it('classifies a hardway roll while a point is on', () => {
    const roll = mkRoll({ dice: [2, 2], phase: 'point', point: 8 })
    const state = rollLogReducer(initialRollLogState(), roll)
    expect(state.rolls[0].type).toBe('hardway')
  })

  it('never clears rolls across a shooter change — just tags each record', () => {
    let state = rollLogReducer(initialRollLogState(), mkRoll({ shooter_index: 0, dice: [3, 4], phase: 'come-out', point: null }))
    state = rollLogReducer(state, mkRoll({ shooter_index: 1, dice: [2, 3], phase: 'come-out', point: null }))
    expect(state.rolls).toHaveLength(2)
    expect(state.rolls.map((r) => r.shooter)).toEqual([0, 1])
  })

  it('classifies consecutive rolls correctly using each envelope\'s own pre-roll point, not a lagging cache', () => {
    // point-set (6) -> point-hit (6) -> point-set (9) -> seven-out.
    // A stale one-roll-behind tracker would misjudge at least one of these.
    let state = initialRollLogState()
    state = rollLogReducer(state, mkRoll({ dice: [2, 4], phase: 'come-out', point: null })) // sets 6
    state = rollLogReducer(state, mkRoll({ dice: [3, 3], phase: 'point', point: 6 })) // hits 6
    state = rollLogReducer(state, mkRoll({ dice: [4, 5], phase: 'come-out', point: null })) // sets 9
    state = rollLogReducer(state, mkRoll({ dice: [3, 4], phase: 'point', point: 9 })) // sevens out
    expect(state.rolls.map((r) => r.type)).toEqual(['point-set', 'point-hit', 'point-set', 'seven-out'])
  })

  it('passes through any non-DiceRolled envelope unchanged', () => {
    const state = initialRollLogState()
    const started: SessionStarted = { type: 'SessionStarted', seq: 0, table_id: 't1', num_shooters: 10 }
    expect(rollLogReducer(state, started as Envelope)).toBe(state)
  })
})
