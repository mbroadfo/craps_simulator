import { describe, expect, it } from 'vitest'
import {
  archPoint,
  bounceOffset,
  computeDieWaypoints,
  LAUNCH,
  pickLandingCenter,
  pipsForFace,
  settleRotationForValue,
  toWorldPosition,
} from './diceLayout'

describe('LAUNCH', () => {
  it('is on the left edge of the felt (dice enter from the left)', () => {
    expect(LAUNCH.x).toBeLessThan(700) // felt's horizontal midpoint
  })
})

describe('pickLandingCenter', () => {
  it('always returns a point right of the launch point (throw travels left to right)', () => {
    for (let i = 0; i < 20; i++) {
      expect(pickLandingCenter().x).toBeGreaterThan(LAUNCH.x)
    }
  })

  it('picks from more than one spot across repeated calls (lands in different places)', () => {
    const seen = new Set<string>()
    for (let i = 0; i < 30; i++) {
      const p = pickLandingCenter()
      seen.add(`${p.x},${p.y}`)
    }
    expect(seen.size).toBeGreaterThan(1)
  })
})

describe('computeDieWaypoints', () => {
  const center = { x: 700, y: 300 }
  const [die1, die2] = computeDieWaypoints(center)

  it('both dice launch from the same shared point', () => {
    expect(die1.launch).toEqual(die2.launch)
    expect(die1.launch).toEqual(LAUNCH)
  })

  it('lands the two dice symmetrically around the chosen landing center', () => {
    expect(die2.landing.x - die1.landing.x).toBeCloseTo(80, 5)
    expect((die1.landing.x + die2.landing.x) / 2).toBeCloseTo(center.x, 5)
    expect(die1.landing.y).toBe(center.y)
    expect(die2.landing.y).toBe(center.y)
  })
})

describe('toWorldPosition', () => {
  it('maps a viewBox point directly onto the ground plane (x, y) -> (x, z)', () => {
    expect(toWorldPosition({ x: 700, y: 425.5 })).toEqual({ x: 700, z: 425.5 })
    expect(toWorldPosition({ x: 0, y: 0 })).toEqual({ x: 0, z: 0 })
  })
})

describe('archPoint', () => {
  const from = { x: 40, z: 400 }
  const to = { x: 900, z: 320 }

  it('starts exactly at the launch point, at ground level', () => {
    expect(archPoint(from, to, 0, 140)).toEqual({ x: from.x, y: 0, z: from.z })
  })

  it('lands exactly at the landing point, at ground level — where a die lands IS where it tumbles to', () => {
    expect(archPoint(from, to, 1, 140)).toEqual({ x: to.x, y: 0, z: to.z })
  })

  it('rises above ground mid-flight (a visible arch, not a flat slide)', () => {
    expect(archPoint(from, to, 0.5, 140).y).toBeGreaterThan(0)
  })

  it('interpolates x/z linearly and monotonically toward the landing point', () => {
    const quarter = archPoint(from, to, 0.25, 140)
    const half = archPoint(from, to, 0.5, 140)
    expect(half.x).toBeGreaterThan(quarter.x)
    expect(half.x).toBeCloseTo((from.x + to.x) / 2, 5)
  })

  it('clamps t outside [0,1] rather than overshooting the landing point', () => {
    expect(archPoint(from, to, 1.5, 140)).toEqual({ x: to.x, y: 0, z: to.z })
    expect(archPoint(from, to, -0.5, 140)).toEqual({ x: from.x, y: 0, z: from.z })
  })
})

describe('bounceOffset', () => {
  it('is zero at both ends of the settle window (never disturbs the exact landing spot)', () => {
    expect(bounceOffset(0, 20, 2.5)).toBe(0)
    expect(bounceOffset(1, 20, 2.5)).toBe(0)
  })

  it('is never negative (a bounce lifts off the ground, never sinks into it)', () => {
    for (let u = 0; u <= 1; u += 0.05) {
      expect(bounceOffset(u, 20, 2.5)).toBeGreaterThanOrEqual(0)
    }
  })

  it('clamps u outside [0,1] to zero', () => {
    expect(bounceOffset(-0.2, 20, 2.5)).toBe(0)
    expect(bounceOffset(1.2, 20, 2.5)).toBe(0)
  })
})

describe('pipsForFace', () => {
  it('returns one centered pip for 1', () => {
    const pips = pipsForFace(1)
    expect(pips).toHaveLength(1)
    expect(pips[0]).toEqual({ x: 24, y: 24, r: 5 })
  })

  it('returns the right pip count for every face 1-6', () => {
    expect(pipsForFace(2)).toHaveLength(2)
    expect(pipsForFace(3)).toHaveLength(3)
    expect(pipsForFace(4)).toHaveLength(4)
    expect(pipsForFace(5)).toHaveLength(5)
    expect(pipsForFace(6)).toHaveLength(6)
  })

  it('places 6 as two columns of three (no center pip)', () => {
    const pips = pipsForFace(6)
    expect(pips.find((p) => p.x === 24 && p.y === 24)).toBeUndefined()
  })

  it('returns no pips for an unknown/out-of-range value', () => {
    expect(pipsForFace(0)).toEqual([])
    expect(pipsForFace(7)).toEqual([])
  })
})

describe('settleRotationForValue', () => {
  it('needs no rotation for 1 (already facing up by definition)', () => {
    expect(settleRotationForValue(1)).toEqual({ x: 0, y: 0, z: 0 })
  })

  it('gives every value 1-6 a distinct rotation', () => {
    const rotations = [1, 2, 3, 4, 5, 6].map((v) => JSON.stringify(settleRotationForValue(v)))
    expect(new Set(rotations).size).toBe(6)
  })

  it('opposite faces (1/6, 2/5, 3/4) rotate around the same axis', () => {
    expect(settleRotationForValue(6).z).not.toBe(0)
    expect(settleRotationForValue(1).z).toBe(0)
    expect(settleRotationForValue(5).z).toBe(-settleRotationForValue(2).z)
    expect(settleRotationForValue(4).x).toBe(-settleRotationForValue(3).x)
  })

  it('falls back to the front face for an out-of-range value', () => {
    expect(settleRotationForValue(0)).toEqual({ x: 0, y: 0, z: 0 })
  })
})
