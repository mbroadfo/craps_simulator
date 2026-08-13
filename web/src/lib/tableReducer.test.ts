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
      if (f.kind === 'return') expect(f.delta).toBe(0)
      else expect(f.kind === 'win' ? f.delta >= 0 : f.delta < 0).toBe(true)
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

// BetStatusChanged already flips ChipStack.status (case 'BetStatusChanged'
// above) — this is the mechanism Come/Don't Come Odds now rely on to
// toggle working/not-working (see craps_engine.py's refresh_bet_statuses()),
// same as Place/Buy/Lay already did. Explicit coverage since it was
// previously only exercised incidentally by the fixture replay.
describe('tableReducer — BetStatusChanged', () => {
  it('flips an existing chip stack\'s status', () => {
    let state = initialState()
    state = tableReducer(state, {
      seq: 0,
      table_id: 't',
      type: 'BetPlaced',
      player_name: 'Bot',
      bet_type: 'Come Odds',
      amount: 50,
      number: 6,
    })
    const before = [...state.chips.values()][0]
    expect(before.status).toBe('active')

    state = tableReducer(state, {
      seq: 1,
      table_id: 't',
      type: 'BetStatusChanged',
      player_name: 'Bot',
      bet_type: 'Come Odds',
      number: 6,
      status: 'inactive',
    })
    const after = [...state.chips.values()][0]
    expect(after.status).toBe('inactive')
  })
})

// Regression test for a real reported bug: craps/table.py's ephemeral-
// odds sweep (removes+re-places an odds bet every roll its parent
// doesn't itself resolve — see three_point_v2.py) publishes a
// BetResolved(status="swept", removed=true) so the chip pop still
// happens (pushChip on BetPlaced always *appends*, never replaces —
// without a pop signal every roll, the displayed pile grows forever
// while the real bet stays correctly bounded server-side). It must
// pop the chip like any other resolved bet, but — unlike a real win
// or loss — must NOT produce a fade-up toast, since the bet never
// actually won or lost.
describe('tableReducer — swept odds bets (ephemeral re-place, not a resolution)', () => {
  it('pops the chip but adds no fade-up for a BetResolved with status="swept"', () => {
    let state = initialState()
    state = tableReducer(state, {
      seq: 0,
      table_id: 't',
      type: 'BetPlaced',
      player_name: 'Bot',
      bet_type: 'Pass Line Odds',
      amount: 40,
      number: null,
    })
    expect([...state.chips.values()].some((s) => s.amounts.includes(40))).toBe(true)

    state = tableReducer(state, {
      seq: 1,
      table_id: 't',
      type: 'BetResolved',
      player_name: 'Bot',
      bet_type: 'Pass Line Odds',
      amount: 40,
      number: null,
      status: 'swept',
      payout: 0,
      win_payout: 0,
      removed: true,
    })

    expect(state.fadeUps.length).toBe(0)
    expect([...state.chips.values()].some((s) => s.amounts.includes(40))).toBe(false)
  })

  it('does not let a swept-then-replaced pile grow across repeated rolls, unlike the bug this guards', () => {
    let state = initialState()
    const place = (seq: number) =>
      tableReducer(state, {
        seq,
        table_id: 't',
        type: 'BetPlaced',
        player_name: 'Bot',
        bet_type: 'Pass Line Odds',
        amount: 40,
        number: null,
      })
    const sweep = (seq: number) =>
      tableReducer(state, {
        seq,
        table_id: 't',
        type: 'BetResolved',
        player_name: 'Bot',
        bet_type: 'Pass Line Odds',
        amount: 40,
        number: null,
        status: 'swept',
        payout: 0,
        win_payout: 0,
        removed: true,
      })

    for (let seq = 0; seq < 10; seq += 2) {
      state = place(seq)
      state = sweep(seq + 1)
    }

    const stack = [...state.chips.values()].find((s) => s.amounts.length > 0)
    expect(stack).toBeUndefined()
  })
})

// Regression test for a real reported bug: a Come Odds bet refunded
// when its parent resolves (off during come-out, or a come-out loss —
// see craps/table.py's attached-bet loops) was indistinguishable from
// a real loss on the felt: BetResolved(status="return") rendered as
// "-$50" in red, even though place_bet() never deducted it and the
// player's bankroll was never touched.
describe('tableReducer — returned odds bets (refund, not a loss)', () => {
  it('pops the chip and adds a zero-delta "return" fade-up, not a loss', () => {
    let state = initialState()
    state = tableReducer(state, {
      seq: 0,
      table_id: 't',
      type: 'BetPlaced',
      player_name: 'Bot',
      bet_type: 'Come Odds',
      amount: 50,
      number: 6,
    })

    state = tableReducer(state, {
      seq: 1,
      table_id: 't',
      type: 'BetResolved',
      player_name: 'Bot',
      bet_type: 'Come Odds',
      amount: 50,
      number: 6,
      status: 'return',
      payout: 0,
      win_payout: 0,
      removed: true,
    })

    expect([...state.chips.values()].some((s) => s.amounts.includes(50))).toBe(false)
    expect(state.fadeUps).toHaveLength(1)
    expect(state.fadeUps[0]).toMatchObject({ kind: 'return', delta: 0 })
  })
})
