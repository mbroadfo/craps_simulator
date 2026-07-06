/**
 * Replay driver against the recorded fixture: stepping, roll beats,
 * and seeks must all agree exactly with a straight reduce of the
 * stream — replay and live are the same renderer.
 */
import { readFileSync } from 'node:fs'
import { join } from 'node:path'
import { describe, expect, it } from 'vitest'

import type { Envelope } from './events'
import { ReplayController } from './replay'
import { initialState, tableReducer, type TableState } from './tableReducer'

const events: Envelope[] = readFileSync(
  join(__dirname, '__fixtures__', 'session.jsonl'),
  'utf-8',
)
  .split('\n')
  .filter((line) => line.trim() !== '')
  .map((line) => JSON.parse(line) as Envelope)

const reduceTo = (seq: number): TableState =>
  events.slice(0, seq + 1).reduce(tableReducer, initialState())

describe('ReplayController', () => {
  it('drains to the same state as a straight reduce', () => {
    const replay = new ReplayController(events)
    while (replay.step()) {
      /* drain */
    }
    expect(replay.atEnd).toBe(true)
    expect(replay.position).toBe(events.length - 1)
    expect(replay.state).toEqual(reduceTo(events.length - 1))
    expect(replay.state.finished).toBe(true)
  })

  it('stepRoll advances one dice roll per call', () => {
    const replay = new ReplayController(events)
    const totalRolls = events.filter((e) => e.type === 'DiceRolled').length

    let beats = 0
    while (!replay.atEnd) {
      const before = replay.state.rollNumber
      replay.stepRoll()
      if (replay.state.rollNumber > before) beats += 1
      expect(replay.state.rollNumber).toBeLessThanOrEqual(before + 1)
    }
    expect(beats).toBe(totalRolls)
  })

  it('seek forward and backward both land exactly', () => {
    const replay = new ReplayController(events)
    const middle = Math.floor(events.length / 2)

    replay.seek(middle)
    expect(replay.position).toBe(middle)
    expect(replay.state).toEqual(reduceTo(middle))

    replay.seek(events.length - 1)
    expect(replay.state).toEqual(reduceTo(events.length - 1))

    replay.seek(10) // scrub backwards
    expect(replay.position).toBe(10)
    expect(replay.state).toEqual(reduceTo(10))
  })

  it('rollCounts distribution matches the stream', () => {
    const replay = new ReplayController(events)
    replay.seek(events.length - 1)

    const expected: Record<number, number> = {}
    for (const e of events) {
      if (e.type === 'DiceRolled') expected[e.total] = (expected[e.total] ?? 0) + 1
    }
    expect(replay.state.rollCounts).toEqual(expected)
    const totalRolls = Object.values(replay.state.rollCounts).reduce((a, b) => a + b, 0)
    expect(totalRolls).toBe(replay.state.rollNumber)
  })
})
