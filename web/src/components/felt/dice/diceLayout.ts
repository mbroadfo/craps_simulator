/**
 * Pure, DOM-free geometry for DiceAnimation — pip layout, the felt-
 * viewBox-to-3D-world coordinate mapping, and the cube rotation that
 * brings a given rolled value's face up to the camera. No Three.js/
 * Cannon-es imports here on purpose: this stays plain-data testable
 * without a WebGL context, which jsdom can't provide (see
 * DiceAnimation.tsx's own note on why its rendering can't be unit
 * tested the same way this can).
 *
 * Both dice enter stacked from the felt's left edge (a simple,
 * predictable arch — see DiceAnimation.tsx's archPosition) and land
 * at a landing *center* picked at random each roll from a small pool
 * of spots scattered across the open interior — between the box-
 * number rail (busiest with chips) and the DC/rail column on the
 * right, roughly spanning the Come/Field bands. This is "avoid bets"
 * without live chip awareness — just cycling through spots that are
 * typically open, so consecutive rolls don't all land in the exact
 * same spot.
 */
export const FELT_VIEWBOX_W = 1400
export const FELT_VIEWBOX_H = 851
/** Printed betting-surface height — excludes the table apron/chip rail below y=724 (see Felt.tsx's own comment on FELT_H_BG). */
const FELT_PLAY_H = 724

/** Left edge of the felt, vertically centered — both dice enter stacked from here. */
export const LAUNCH: Point = { x: 40, y: FELT_PLAY_H / 2 }

/** Candidate landing centers, scattered across the open Come/Field interior — chosen at random per roll (see pickLandingCenter). */
const LANDING_POOL: Point[] = [
  { x: 620, y: 300 },
  { x: 750, y: 330 },
  { x: 950, y: 300 },
  { x: 1080, y: 340 },
  { x: 800, y: 460 },
]

export interface Point {
  x: number
  y: number
}

export interface DieWaypoints {
  launch: Point
  landing: Point
}

export function pickLandingCenter(): Point {
  return LANDING_POOL[Math.floor(Math.random() * LANDING_POOL.length)]
}

// Both dice share one landing *center* (picked once per roll) offset
// ±40 so they land as a pair, not on top of each other. DiceAnimation.tsx
// builds the actual flight arc from just these two endpoints (launch,
// landing) — no bezier control point needed here.
export function computeDieWaypoints(landingCenter: Point): [DieWaypoints, DieWaypoints] {
  return [
    { launch: LAUNCH, landing: { x: landingCenter.x - 40, y: landingCenter.y } },
    { launch: LAUNCH, landing: { x: landingCenter.x + 40, y: landingCenter.y } },
  ]
}

/**
 * Maps a felt-viewBox point directly onto the 3D scene's ground plane
 * (world x/z — world y is height, scripted per-frame in
 * DiceAnimation.tsx's archPosition). Deliberately an identity mapping
 * (world units == viewBox units, no rescaling): the orthographic
 * camera's frustum in DiceAnimation.tsx is sized to exactly
 * [0,FELT_VIEWBOX_W]x[0,FELT_VIEWBOX_H], so a die's world position
 * lines up with the same coordinates every other felt element already
 * uses (layout.ts's COME, FIELD, etc.) — no separate scale factor to
 * keep in sync.
 */
export function toWorldPosition(point: Point): { x: number; z: number } {
  return { x: point.x, z: point.y }
}

const POSITIONS = {
  TL: { x: 12, y: 12 },
  TR: { x: 36, y: 12 },
  ML: { x: 12, y: 24 },
  MR: { x: 36, y: 24 },
  BL: { x: 12, y: 36 },
  BR: { x: 36, y: 36 },
  C: { x: 24, y: 24 },
} as const

type PositionKey = keyof typeof POSITIONS

const FACE_POINTS: Record<number, PositionKey[]> = {
  1: ['C'],
  2: ['TL', 'BR'],
  3: ['TL', 'C', 'BR'],
  4: ['TL', 'TR', 'BL', 'BR'],
  5: ['TL', 'TR', 'C', 'BL', 'BR'],
  6: ['TL', 'TR', 'ML', 'MR', 'BL', 'BR'],
}

const FACE_RADIUS: Record<number, number> = { 1: 5, 2: 4, 3: 4, 4: 3.5, 5: 3.5, 6: 3 }

export interface Pip extends Point {
  r: number
}

/** The pips (position + radius, in a 0-48 face-local box) for a die face showing `value` (1-6). Unknown/out-of-range values render no pips rather than throwing. Used to draw each face's CanvasTexture in DiceAnimation.tsx. */
export function pipsForFace(value: number): Pip[] {
  const points = FACE_POINTS[value]
  if (!points) return []
  const r = FACE_RADIUS[value]
  return points.map((key) => ({ ...POSITIONS[key], r }))
}

/**
 * The camera looks straight down (-Y) at the ground plane, so the
 * face that reads at rest is whichever one points toward +Y ("up").
 * Values are assigned to cube axes with opposite faces summing to 7,
 * like a real die: +Y=1/-Y=6, +X=2/-X=5, +Z=3/-Z=4 (the axis
 * assignment itself is arbitrary beyond that constraint — see
 * DiceAnimation.tsx's materials array, which must list textures in
 * this same order: Three.js's BoxGeometry material slots are
 * [+X,-X,+Y,-Y,+Z,-Z]).
 *
 * Each entry is the Euler rotation (degrees) that brings that value's
 * face from its natural axis position to +Y — i.e. the inverse of
 * that face's own placement rotation. Derived by hand from Three.js's
 * standard right-hand-rule rotation convention (NOT the same sign
 * convention CSS's rotateX/rotateY use — Phase A's cube used CSS
 * transforms and had a different, incompatible table; don't reuse
 * those signs here).
 */
const SETTLE_ROTATION: Record<number, { x: number; y: number; z: number }> = {
  1: { x: 0, y: 0, z: 0 }, // already +Y
  6: { x: 0, y: 0, z: 180 }, // -Y, opposite of 1
  2: { x: 0, y: 0, z: 90 }, // +X -> +Y
  5: { x: 0, y: 0, z: -90 }, // -X -> +Y, opposite of 2
  3: { x: -90, y: 0, z: 0 }, // +Z -> +Y
  4: { x: 90, y: 0, z: 0 }, // -Z -> +Y, opposite of 3
}

/** The cube rotation (Euler degrees) that brings `value`'s face to point up at the camera. Falls back to showing 1 (no rotation) for an out-of-range value — should never happen with a real DiceRolled result, but keeps this total rather than throwing. */
export function settleRotationForValue(value: number): { x: number; y: number; z: number } {
  return SETTLE_ROTATION[value] ?? { x: 0, y: 0, z: 0 }
}

/** A die's position on the 3D scene's ground plane (post-toWorldPosition world x/z). */
export interface GroundPoint {
  x: number
  z: number
}

/**
 * A die's ground-plane position along a simple straight-line arc from
 * `from` to `to`, at fraction `t` (0=start, 1=landed) — height is a
 * parabola peaking at `peakHeight` above the ground at the arc's
 * midpoint and returning to exactly 0 at t=1. archPoint(from, to, 1,
 * _) always equals `to` exactly, by construction — the earlier
 * physics-simulated flight only ever *aimed* to land there (real
 * rigid-body collision physics can't be trusted to hit an exact spot,
 * and in practice a solver instability sent dice flying off the felt
 * instead), so no clamp or force-snap is needed here: the landing
 * spot IS what the die tumbles to, because the formula's own
 * end-of-arc value is that landing spot.
 */
export function archPoint(
  from: GroundPoint,
  to: GroundPoint,
  t: number,
  peakHeight: number,
): { x: number; y: number; z: number } {
  const c = Math.min(Math.max(t, 0), 1)
  return {
    x: from.x + (to.x - from.x) * c,
    y: peakHeight * 4 * c * (1 - c),
    z: from.z + (to.z - from.z) * c,
  }
}

/**
 * A small decaying bounce-in-place height offset for the settle
 * window after the arc lands (u=0 at landing, u=1 once fully
 * settled) — purely decorative on top of archPoint's y=0 at t=1.
 * Never negative (a bounce lifts off the ground, it doesn't sink into
 * it) and exactly 0 at both ends, so it never disturbs the exact
 * landing position it's layered on top of.
 */
export function bounceOffset(u: number, height: number, cycles: number): number {
  const c = Math.min(Math.max(u, 0), 1)
  if (c <= 0 || c >= 1) return 0
  return height * (1 - c) * Math.abs(Math.sin(c * Math.PI * cycles))
}
