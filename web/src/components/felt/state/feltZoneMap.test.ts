import { describe, expect, it } from 'vitest'
import { feltZoneFor } from './feltZoneMap'

describe('feltZoneFor', () => {
  it('maps line bets to their static band zones', () => {
    expect(feltZoneFor('Pass Line', null)?.zoneId).toBe('passline')
    expect(feltZoneFor("Don't Pass", null)?.zoneId).toBe('dontpass')
  })

  it('maps odds bets (either side) to the one shared dev-tool zone', () => {
    expect(feltZoneFor('Pass Line Odds', 6)?.zoneId).toBe('passline-odds')
    expect(feltZoneFor("Don't Pass Odds", 4)?.zoneId).toBe('passline-odds')
  })

  it('maps Come/Don\'t Come to their own box before traveling', () => {
    expect(feltZoneFor('Come', null)?.zoneId).toBe('come')
    expect(feltZoneFor("Don't Come", null)?.zoneId).toBe('dontcome')
  })

  it('maps a traveled Come/Don\'t Come to its own offset pile, distinct from Place/Lay', () => {
    expect(feltZoneFor('Come', 6)?.zoneId).toBe('come-6')
    expect(feltZoneFor("Don't Come", 4)?.zoneId).toBe('dontcome-4')
    expect(feltZoneFor('Come Odds', 8)?.zoneId).toBe('come-8')
    expect(feltZoneFor("Don't Come Odds", 10)?.zoneId).toBe('dontcome-10')

    // Genuinely distinct positions, not just distinct ids sharing a spot.
    const place6 = feltZoneFor('Place', 6)!
    const come6 = feltZoneFor('Come', 6)!
    expect(come6.y).toBe(place6.y)
    expect(come6.x).not.toBe(place6.x)
  })

  it('maps Place/Buy to the bottom strip and Lay/Don\'t Place to the top strip, per number', () => {
    for (const n of [4, 5, 6, 8, 9, 10]) {
      expect(feltZoneFor('Place', n)?.zoneId).toBe(`place-${n}`)
      expect(feltZoneFor('Buy', n)?.zoneId).toBe(`place-${n}`)
      expect(feltZoneFor('Lay', n)?.zoneId).toBe(`laydc-${n}`)
      expect(feltZoneFor("Don't Place", n)?.zoneId).toBe(`laydc-${n}`)
    }
  })

  it('maps Field to its own zone', () => {
    expect(feltZoneFor('Field', null)?.zoneId).toBe('field')
  })

  it('maps every hardway number to its pair-N-N cell', () => {
    expect(feltZoneFor('Hardways', 6)?.zoneId).toBe('pair-3-3')
    expect(feltZoneFor('Hardways', 8)?.zoneId).toBe('pair-4-4')
    expect(feltZoneFor('Hardways', 4)?.zoneId).toBe('pair-2-2')
    expect(feltZoneFor('Hardways', 10)?.zoneId).toBe('pair-5-5')
  })

  it('maps a hop pair regardless of the tuple\'s order', () => {
    const forward = feltZoneFor('Hop', [3, 3])
    expect(forward?.zoneId).toBe('hop-3-3')
    expect(feltZoneFor('Hop', [1, 6])?.zoneId).toBe('hop-1-6')
    // engine order (b, a) resolves to the same felt cell as (a, b)
    expect(feltZoneFor('Hop', [4, 1])?.zoneId).toBe(feltZoneFor('Hop', [1, 4])?.zoneId)
  })

  it('maps All/Tall/Small to their named ATS cells, not a literal string match', () => {
    expect(feltZoneFor('All', null)?.zoneId).toBe("ats-Make'Em All")
    expect(feltZoneFor('Tall', null)?.zoneId).toBe('ats-All Tall')
    expect(feltZoneFor('Small', null)?.zoneId).toBe('ats-All Small')
  })

  it('maps dormant-but-zoned bet types (Horn, Any Craps)', () => {
    expect(feltZoneFor('Horn', null)?.zoneId).toBe('horn-bet')
    expect(feltZoneFor('Any Craps', null)?.zoneId).toBe("band-Any Craps")
  })

  it('returns null for bet types with no felt zone at all, never throws', () => {
    expect(feltZoneFor('Proposition', null)).toBeNull()
    expect(feltZoneFor('World', null)).toBeNull()
    expect(feltZoneFor('Repeater', 6)).toBeNull()
    expect(feltZoneFor('Something Unknown', null)).toBeNull()
  })

  it('returns null for a Come/Place-family bet type with no number when one is required', () => {
    expect(feltZoneFor('Place', null)).toBeNull()
    expect(feltZoneFor('Lay', null)).toBeNull()
    expect(feltZoneFor('Hop', null)).toBeNull()
  })
})
