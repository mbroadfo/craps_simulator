import { describe, expect, it } from 'vitest'
import type { RollRecord } from '../types'
import { currentShooterRolls } from './currentShooterRolls'

function roll(shooter: number, total: number, type: RollRecord['type'] = 'neutral'): RollRecord {
  return { shooter, d1: 1, d2: total - 1, total, type }
}

describe('currentShooterRolls', () => {
  it('returns an empty list for no rolls', () => {
    expect(currentShooterRolls([])).toEqual([])
  })

  it('returns every roll when no seven-out has happened yet', () => {
    const rolls = [roll(1, 5, 'point-set'), roll(1, 8, 'neutral'), roll(1, 5, 'point-hit')]
    expect(currentShooterRolls(rolls)).toEqual(rolls)
  })

  it('keeps a seven-out visible as the last roll of its own shooter, even though the live shooter index has already advanced', () => {
    const rolls = [roll(1, 6, 'point-set'), roll(1, 7, 'seven-out')]
    // The whole array is shooter 1's group — the seven-out that just
    // happened must still show, not vanish the instant it arrives.
    expect(currentShooterRolls(rolls)).toEqual(rolls)
  })

  it('resets to only the new shooter\'s rolls once the next roll actually arrives', () => {
    const rolls = [roll(1, 6, 'point-set'), roll(1, 7, 'seven-out'), roll(2, 9, 'point-set')]
    expect(currentShooterRolls(rolls)).toEqual([roll(2, 9, 'point-set')])
  })

  it('handles back-to-back seven-outs (a shooter who sevens out on the come-out roll)', () => {
    const rolls = [roll(1, 7, 'seven-out'), roll(2, 7, 'seven-out')]
    expect(currentShooterRolls(rolls)).toEqual([roll(2, 7, 'seven-out')])
  })
})
