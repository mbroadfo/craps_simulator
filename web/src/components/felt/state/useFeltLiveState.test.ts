import { describe, expect, it } from 'vitest'
import type { ChipStack, FadeUp } from '../../../lib/tableReducer'
import { buildChipZones, buildToastBuckets } from './useFeltLiveState'

function stack(overrides: Partial<ChipStack>): ChipStack {
  return { player: 'Molly', betType: 'Come Odds', number: 6, amounts: [50], status: 'active', ...overrides }
}

function fadeUp(overrides: Partial<FadeUp>): FadeUp {
  return { seq: 0, player: 'Molly', betType: 'Come Odds', number: 6, delta: 0, kind: 'return', ...overrides }
}

describe('buildChipZones', () => {
  it('carries an active stack\'s status onto its zone', () => {
    const chips = new Map([['k1', stack({ status: 'active' })]])
    const zones = buildChipZones(chips, 'Molly')
    const zone = Object.values(zones)[0]
    expect(zone.status).toBe('active')
  })

  it('carries an inactive stack\'s status onto its zone', () => {
    const chips = new Map([['k1', stack({ status: 'inactive' })]])
    const zones = buildChipZones(chips, 'Molly')
    const zone = Object.values(zones)[0]
    expect(zone.status).toBe('inactive')
  })

  it('reads inactive when merging one active and one inactive stack at the same zone', () => {
    // Two Come bets can legitimately land on the same number/zone —
    // if either part of the pile is off, the whole merged pile must
    // read as inactive (dimmed), not just the half that's off.
    const chips = new Map([
      ['k1', stack({ status: 'active' })],
      ['k2', stack({ status: 'inactive' })],
    ])
    const zones = buildChipZones(chips, 'Molly')
    expect(Object.keys(zones)).toHaveLength(1)
    expect(Object.values(zones)[0].status).toBe('inactive')
  })

  it('ignores stacks belonging to another player', () => {
    const chips = new Map([['k1', stack({ player: 'Someone Else' })]])
    const zones = buildChipZones(chips, 'Molly')
    expect(zones).toEqual({})
  })

  it('drops stacks with no felt zone mapping', () => {
    const chips = new Map([['k1', stack({ betType: 'Repeater', number: null })]])
    const zones = buildChipZones(chips, 'Molly')
    expect(zones).toEqual({})
  })
})

describe('buildToastBuckets', () => {
  it('a lone return resolution nets to a zero-amount "return" bucket', () => {
    const buckets = buildToastBuckets([fadeUp({ kind: 'return', delta: 0 })], 'Molly')
    expect(buckets).toEqual([{ x: expect.any(Number), y: expect.any(Number), amount: 0, kind: 'return' }])
  })

  it('a lone loss resolution is a "loss" bucket', () => {
    const buckets = buildToastBuckets([fadeUp({ kind: 'loss', delta: -50 })], 'Molly')
    expect(buckets[0]).toMatchObject({ amount: -50, kind: 'loss' })
  })

  it('a lone win resolution is a "win" bucket', () => {
    const buckets = buildToastBuckets([fadeUp({ kind: 'win', delta: 14 })], 'Molly')
    expect(buckets[0]).toMatchObject({ amount: 14, kind: 'win' })
  })

  it('merging a real loss with a return in the same neighborhood nets to the real loss, not "return"', () => {
    // A real loss and a refund landing in the same felt zone on the
    // same roll (in spirit: a Come bet losing alongside a separately-
    // resolved return sharing its neighborhood) must net to the true
    // loss, not get mislabeled "Returned" just because one of the two
    // resolutions folded in was a refund.
    const buckets = buildToastBuckets(
      [
        fadeUp({ betType: 'Come Odds', number: 6, kind: 'loss', delta: -10 }),
        fadeUp({ betType: 'Come Odds', number: 6, kind: 'return', delta: 0 }),
      ],
      'Molly',
    )
    expect(buckets).toHaveLength(1)
    expect(buckets[0]).toMatchObject({ amount: -10, kind: 'loss' })
  })

  it('ignores fade-ups belonging to another player', () => {
    const buckets = buildToastBuckets([fadeUp({ player: 'Someone Else' })], 'Molly')
    expect(buckets).toEqual([])
  })
})
