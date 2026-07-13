import { describe, expect, it } from 'vitest'
import type {
  BetResolved,
  DiceRolled,
  PointEstablished,
  PointHit,
  SessionFinalized,
  SevenOut,
  ShooterAssigned,
} from '../../../lib/events'
import { initialPlayByPlay, playByPlayReducer } from './playByPlay'

describe('playByPlayReducer', () => {
  it('starts empty', () => {
    expect(initialPlayByPlay()).toEqual([])
  })

  it('narrates a shooter change', () => {
    const e: ShooterAssigned = { type: 'ShooterAssigned', seq: 0, table_id: 't1', shooter_index: 0, shooter_name: 'Molly' }
    expect(playByPlayReducer([], e)).toEqual(['— Molly is up —'])
  })

  it('narrates a dice roll', () => {
    const e: DiceRolled = {
      type: 'DiceRolled',
      seq: 1,
      table_id: 't1',
      shooter_index: 0,
      roll_number: 1,
      dice: [3, 4],
      total: 7,
      phase: 'come-out',
      point: null,
      table_risk: 0,
      shooter_name: 'Molly',
    }
    expect(playByPlayReducer([], e)).toEqual(['Molly rolls 3-4 (7)'])
  })

  it('narrates point established/hit and seven-out', () => {
    const established: PointEstablished = { type: 'PointEstablished', seq: 2, table_id: 't1', point: 6 }
    const hit: PointHit = { type: 'PointHit', seq: 3, table_id: 't1', point: 6 }
    const sevenOut: SevenOut = { type: 'SevenOut', seq: 4, table_id: 't1', shooter_index: 0, shooter_results: [] }
    let lines = playByPlayReducer([], established)
    expect(lines).toEqual(['Point is 6'])
    lines = playByPlayReducer(lines, hit)
    expect(lines).toEqual(['Point is 6', 'Point made — 6 winners paid'])
    lines = playByPlayReducer(lines, sevenOut)
    expect(lines.at(-1)).toBe('Seven out')
  })

  it('narrates a bet win with a plain-number label', () => {
    const e: BetResolved = {
      type: 'BetResolved',
      seq: 5,
      table_id: 't1',
      player_name: 'Crosstopher',
      bet_type: 'Place',
      amount: 6,
      number: 6,
      status: 'won',
      payout: 14,
      win_payout: 14,
      removed: false,
    }
    expect(playByPlayReducer([], e)).toEqual(['Crosstopher wins $14 on Place 6'])
  })

  it('narrates a bet loss with a hop-pair label', () => {
    const e: BetResolved = {
      type: 'BetResolved',
      seq: 6,
      table_id: 't1',
      player_name: 'Linus',
      bet_type: 'Hop',
      amount: 5,
      number: [3, 3],
      status: 'lost',
      payout: 0,
      win_payout: 0,
      removed: true,
    }
    expect(playByPlayReducer([], e)).toEqual(['Linus loses $5 on Hop 3-3'])
  })

  it('narrates session end', () => {
    const e: SessionFinalized = { type: 'SessionFinalized', seq: 7, table_id: 't1', session_rolls: 93 }
    expect(playByPlayReducer([], e)).toEqual(['Session complete — 93 rolls'])
  })

  it('ignores uninteresting event types', () => {
    expect(playByPlayReducer(['x'], { type: 'BetsRequested', seq: 8, table_id: 't1' })).toEqual(['x'])
  })

  it('caps at 300 lines, dropping the oldest', () => {
    let lines: string[] = []
    for (let i = 0; i < 305; i++) {
      lines = playByPlayReducer(lines, { type: 'ShooterAssigned', seq: i, table_id: 't1', shooter_index: i, shooter_name: `P${i}` })
    }
    expect(lines).toHaveLength(300)
    expect(lines[0]).toBe('— P5 is up —')
    expect(lines.at(-1)).toBe('— P304 is up —')
  })
})
