/**
 * Layout geometry ported verbatim from prototype/parametric-felt.html.
 * These numbers are the product of many rounds of visual iteration —
 * treat them as opaque constants, not something to "clean up." Path
 * data strings in particular must never be hand-retyped (see the
 * plan's Risk #2): copy-paste only, straight from the source file.
 */

export const RAIL = { x: 16, w: 390 } // left column

export const ATS = { x: 16, y: 16, w: 390, h: 140 }
export const HOPS = { x: 16, y: 164, w: 390, h: 228 }
export const PROPS = { x: 16, y: 400, w: 390, h: 330 } // Any Craps bottom lands on y=724, flush with Pass Line

// DC caps only the Don't Pass lane — Pass Line's own top-right column
// runs the full height of the betting area, from y=16 past DC down to
// the rail (see PASS_FILL_D), so DC sits shifted left by Pass Line's
// lane width (53px) to clear that column. Box row narrows to make room
// for DC's left edge; Come/Field keep their original width (they're
// below DC's row, unaffected) — DC's leftover overhang (x 1225..1278)
// just sits above them, same as the box numbers do.
export const DC = { x: 1225, y: 16, w: 106, h: 240 }
export const BOX = {
  x0: 414,
  y: 16,
  w: (DC.x - 6 - 414 - 5 * 6) / 6,
  h: 240,
  gap: 6,
  nums: [4, 5, 6, 8, 9, 10] as const,
}
export const COME = { x: 414, y: 262, w: 858, h: 142 }
export const FIELD = { x: 414, y: 410, w: 858, h: 200 }

export const BOX_WORD: Record<number, string> = { 6: 'Six', 9: 'Nine' } // only Six and Nine

export const TALL_NUMS = [8, 9, 10, 11, 12]
export const SMALL_NUMS = [2, 3, 4, 5, 6]

// Hop grid: unordered pairs only, arranged by point-number column.
// kind: "hard" (amber 30:1) | "easy" (bone 15:1) | "seven" (red 15:1)
export type HopKind = 'hard' | 'easy' | 'seven'
export const HOP_SEVEN: [number, number][] = [
  [1, 6],
  [2, 5],
  [3, 4],
]
export const HOP_GRID: [number, number, HopKind][][] = [
  // row 2 — hardways where the number has one
  [
    [2, 2, 'hard'],
    [1, 4, 'easy'],
    [3, 3, 'hard'],
    [4, 4, 'hard'],
    [4, 5, 'easy'],
    [5, 5, 'hard'],
  ],
  // row 3 — easy ways
  [
    [3, 1, 'easy'],
    [2, 3, 'easy'],
    [2, 4, 'easy'],
    [3, 5, 'easy'],
    [3, 6, 'easy'],
    [4, 6, 'easy'],
  ],
]
// row 4: cols 4/5 merge into "HOP", 6 & 8 third combos, cols 9/10 merge into "BET"
export const HOP_ROW4 = { six: [1, 5] as [number, number], eight: [2, 6] as [number, number] }

// ============================================================
// Chip rail — horizontal, right-justified to the table's own right
// edge, wood-body/two-groove/divider cross-section (90px thick).
// ============================================================
export const RAIL_ORDER = [500, 100, 25, 5, 1] // highest denomination first
export const CHIP_W = 7
export const CHIP_H = 42
export const CHIP_PITCH = 9
export const GROUP_GAP = CHIP_PITCH - CHIP_W // no extra gap between denominations

// Pass Line's own outer edge — not derivable from DC (which sits
// inboard of it, see DC's comment above), so this is fixed to match
// PASS_FILL_D's actual right edge (1384).
export const TABLE_RIGHT_X = 1384
export const RAIL_W = 700
export const RAIL_H = 90
export const RAIL_X1 = TABLE_RIGHT_X
export const RAIL_X0 = RAIL_X1 - RAIL_W // P1: right-justified
export const RAIL_Y0 = 752 // Pass Line's own bottom edge is y=724 — halved that 55px gap down to ~28px

// A chip's edge print (visible from directly above, looking down on
// the rim) is a repeating ring of alternating color/white segments —
// more like 8-10 segments going all the way around, not 3. Standing on
// edge in the tray, each chip shows a run of that ring, and because
// chips are dropped in at different spins around their own vertical
// axis (not tilted — they still sit perfectly flat against their
// neighbors), the run you see doesn't line up chip-to-chip. These are
// the 7-band runs a chip can show — cycled (not randomized) by index
// so the render stays stable, not flickering on every redraw.
export const CHIP_PATTERNS: ('c' | 'w')[][] = [
  ['c', 'w', 'c', 'w', 'c', 'w', 'c'],
  ['w', 'c', 'w', 'c', 'w', 'c', 'w'],
  ['c', 'c', 'w', 'c', 'w', 'c', 'w'],
  ['w', 'c', 'c', 'w', 'c', 'w', 'c'],
  ['c', 'w', 'w', 'c', 'w', 'c', 'c'],
  ['w', 'w', 'c', 'w', 'c', 'w', 'c'],
  ['c', 'w', 'c', 'c', 'w', 'w', 'c'],
  ['w', 'c', 'w', 'w', 'c', 'c', 'w'],
]

// ============================================================
// Felt shell — static SVG path data (BANDS v6). Pass Line and Don't
// Pass are both 53px wrap-around lanes hugging the right + bottom
// edges. Pass Line's lane runs the FULL height of the betting area
// (from y=16, past the Don't Come box) so it reaches the top — Don't
// Come no longer caps it, only Don't Pass's lane still terminates at
// Don't Come's bottom edge (y=256).
// ============================================================
export const PASS_FILL_D = `M 1341,16 L 1374,16 A 10,10 0 0 1 1384,26
           L 1384,676 A 48,48 0 0 1 1336,724
           L 424,724 A 10,10 0 0 1 414,714
           L 414,676 A 10,10 0 0 1 424,671
           L 1307,671 A 24,24 0 0 0 1331,647
           L 1331,26 A 10,10 0 0 1 1341,16 Z`

export const DONTPASS_FILL_D = `M 1286,264 L 1323,264 A 8,8 0 0 1 1331,272
           L 1331,647 A 24,24 0 0 1 1307,671
           L 422,671 A 8,8 0 0 1 414,663
           L 414,626 A 8,8 0 0 1 422,618
           L 1258,618 A 20,20 0 0 0 1278,598
           L 1278,272 A 8,8 0 0 1 1286,264 Z`

// Pass Line odds have no printed felt zone on a real table — players
// stack them on the open felt behind their flat bet, between the Pass
// Line's own printed edge and the rail, never on the printed Pass Line
// area itself. This is ONLY a dev-tool click target, sitting in that
// open margin (y 726..742, below Pass Line's y=724 outer edge).
export const PASSLINE_ODDS_FILL = { x: 1060, y: 726, w: 80, h: 16 }

export const FELT_VIEWBOX = '0 0 1400 851'
export const FELT_W = 1400
export const FELT_H_BG = 743 // background/rail rects extend a bit past the printed area (y=724) as "table apron"
