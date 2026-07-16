/**
 * The client's replay gate: a real recorded engine session (seeded,
 * checked in as a fixture) drives the reducer, and the resulting state
 * must agree with the stream's own bookkeeping. This is the same
 * discipline as scripts/verify_replay.py and the Python ChipTracker —
 * if an engine event ever arrives that the reducer can't attribute to
 * a chip it knows about, this test fails.
 */
import { readFileSync } from 'node:fs'
import { join } from 'node:path'
import { describe, expect, it } from 'vitest'

import type { BankrollsUpdated, DiceRolled, Envelope, RiskUpdated } from './events'
import { initialState, tableReducer } from './tableReducer'

const fixturePath = join(__dirname, '__fixtures__', 'session.jsonl')

function loadFixture(): Envelope[] {
  return readFileSync(fixturePath, 'utf-8')
    .split('\n')
    .filter((line) => line.trim() !== '')
    .map((line) => JSON.parse(line) as Envelope)
}

describe('tableReducer replay gate', () => {
  const events = loadFixture()
  const final = events.reduce(tableReducer, initialState())

  it('replays a full recorded session without orphan chip events', () => {
    expect(final.orphans).toEqual([])
  })

  it('has contiguous seq numbers from 0', () => {
    events.forEach((e, i) => expect(e.seq).toBe(i))
  })

  it('finishes the session', () => {
    expect(final.finished).toBe(true)
    expect(final.tableId).toBe('fixture')
    expect(final.numShooters).toBe(8)
  })

  it('counts every roll', () => {
    const rolls = events.filter((e) => e.type === 'DiceRolled')
    expect(rolls.length).toBeGreaterThan(0)
    expect(final.rollNumber).toBe(rolls.length)
  })

  it('ends with bankrolls equal to the last BankrollsUpdated', () => {
    const last = events
      .filter((e): e is BankrollsUpdated => e.type === 'BankrollsUpdated')
      .at(-1)!
    for (const [name, balance] of last.bankrolls) {
      expect(final.players.get(name)?.bankroll).toBe(balance)
    }
    expect(final.players.size).toBe(4)
  })

  it('keeps the full session\'s bankroll history uncapped, one entry per BankrollsUpdated', () => {
    const updates = events.filter((e): e is BankrollsUpdated => e.type === 'BankrollsUpdated')
    for (const player of final.players.values()) {
      expect(player.history.length).toBe(updates.length)
      expect(player.history.at(-1)).toBe(player.bankroll)
    }
  })

  it('keeps the full session\'s at-risk history uncapped, index-aligned with bankroll history', () => {
    const updates = events.filter((e): e is RiskUpdated => e.type === 'RiskUpdated')
    for (const player of final.players.values()) {
      expect(player.atRiskHistory.length).toBe(updates.length)
      expect(player.atRiskHistory.length).toBe(player.history.length)
      expect(player.atRiskHistory.at(-1)).toBe(player.atRisk)
    }
  })

  it('produces one fade-up per resolution', () => {
    const resolutions = events.filter((e) => e.type === 'BetResolved')
    expect(final.fadeUps.length).toBe(resolutions.length)
    for (const f of final.fadeUps) {
      expect(f.win ? f.delta >= 0 : f.delta < 0).toBe(true)
    }
  })

  it('never leaves an empty chip stack behind', () => {
    for (const stack of final.chips.values()) {
      expect(stack.amounts.length).toBeGreaterThan(0)
      for (const amount of stack.amounts) expect(amount).toBeGreaterThan(0)
    }
  })

  it('tracks the puck through the whole stream', () => {
    let state = initialState()
    for (const e of events) {
      state = tableReducer(state, e)
      if (e.type === 'DiceRolled') {
        const roll = e as DiceRolled
        expect(state.puckOn).toBe(roll.phase === 'point')
      }
    }
  })
})
