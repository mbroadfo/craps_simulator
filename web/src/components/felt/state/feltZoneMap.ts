/**
 * Translates a live wire bet (bet_type + number, see web/src/lib/
 * tableReducer.ts's ChipStack) into a felt chip zone id + anchor
 * (Step 3, spectator mode). Anchors are computed from the same
 * layout.ts geometry constants — and the same formulas — the panel
 * components themselves use, so this stays correct if that geometry
 * ever moves; never hand-retype a coordinate here.
 *
 * The felt was never drawn with a printed slot for a traveled Come/
 * Don't Come bet the way a real table has one (tucked in a number's
 * corner) — so a traveled Come/Don't Come renders as its own pile
 * offset toward the left edge of the same box, distinct from a
 * Place/Lay bet's centered pile in that box. Not pixel-accurate to a
 * real felt's corner marker, but enough that "which pile is which"
 * stops being a guess — merging them into one shared pile (the
 * original approach) made a Come bet with odds visually
 * indistinguishable from a Place bet, which is exactly what Mike
 * flagged as confusing once he watched it live.
 *
 * Bet types with no felt zone at all (dormant engine vocabulary no
 * wired strategy currently emits — Proposition, World, Repeater, etc.)
 * resolve to null; callers should skip the bet, not throw, mirroring
 * tableReducer's own `orphans` philosophy.
 */
import type { BetNumber } from '../../../lib/events'
import { ATS, BOX, COME, DC, FIELD, HOPS, HOP_GRID, HOP_ROW4, HOP_SEVEN, PASSLINE_ODDS_FILL, PROPS } from '../layout'

export interface FeltZone {
  zoneId: string
  x: number
  y: number
}

// BoxCell's own outer-zone tooltip (BoxNumbers.tsx) documents the box
// as three rows: "top: place/buy · center: come point + odds ·
// bottom: lay/don't-come" — Place sits in the bottom strip, Lay in
// the top strip (see BoxCell's placeZone/layZone, which these `place`/
// `laydc` y's mirror exactly), and a traveled Come/Don't Come (with
// its odds) belongs in the open CENTER row alongside the box's big
// number, not sharing Place's row. It used to: `come`/`dontcome` here
// reused `place`'s exact y (just offset in x), so a traveled Come bet
// visually read as sitting in the Place strip — a real, reported bug,
// not a style nit.
//
// Within that center row: COME_OFFSET_X shifts the base Come/Don't
// Come pile off dead-center so it doesn't sit directly on the big
// number. The Odds pile then shifts right+down from *that* — the
// exact same relative offset Pass Line Odds already uses from Pass
// Line itself (PASSLINE_ODDS_FILL: +20 x, +37 y from the Pass Line
// zone), reused here rather than invented fresh, so every "bet + its
// odds" pair reads the same way across the felt.
const COME_OFFSET_X = 32
const COME_ODDS_DX = 20
const COME_ODDS_DY = 37

interface BoxZoneSet {
  place: FeltZone
  laydc: FeltZone
  come: FeltZone
  dontcome: FeltZone
  comeOdds: FeltZone
  dontcomeOdds: FeltZone
}

function boxZones(): Map<number, BoxZoneSet> {
  const topH = 42
  const botH = 42
  const y1 = BOX.y + topH
  const y2 = BOX.y + BOX.h - botH
  const midY = BOX.y + topH + (BOX.h - topH - botH) / 2
  const map = new Map<number, BoxZoneSet>()
  BOX.nums.forEach((n, i) => {
    const x = BOX.x0 + i * (BOX.w + BOX.gap)
    const cx = x + BOX.w / 2
    map.set(n, {
      place: { zoneId: `place-${n}`, x: cx, y: y2 + botH / 2 },
      laydc: { zoneId: `laydc-${n}`, x: cx, y: y1 - topH / 2 },
      come: { zoneId: `come-${n}`, x: cx - COME_OFFSET_X, y: midY },
      dontcome: { zoneId: `dontcome-${n}`, x: cx - COME_OFFSET_X, y: midY },
      comeOdds: { zoneId: `come-odds-${n}`, x: cx - COME_OFFSET_X + COME_ODDS_DX, y: midY + COME_ODDS_DY },
      dontcomeOdds: { zoneId: `dontcome-odds-${n}`, x: cx - COME_OFFSET_X + COME_ODDS_DX, y: midY + COME_ODDS_DY },
    })
  })
  return map
}

// Unordered-pair key ("min-max") -> the zone as HopsPanel actually
// built it (its zoneId keeps the source array's own a/b order, not a
// normalized one — only the lookup key is normalized).
function hopZones(): Map<string, FeltZone> {
  const gx = HOPS.x + 3
  const gy = HOPS.y + 3
  const cw = (HOPS.w - 6) / 6
  const ch = (HOPS.h - 6) / 4
  const r4y = gy + ch * 3
  const map = new Map<string, FeltZone>()
  const add = (a: number, b: number, x: number, y: number, w: number, h: number) => {
    const key = `${Math.min(a, b)}-${Math.max(a, b)}`
    map.set(key, { zoneId: `hop-${a}-${b}`, x: x + w / 2, y: y + h / 2 - 10 })
  }

  HOP_SEVEN.forEach(([a, b], i) => add(a, b, gx + i * cw * 2, gy, cw * 2, ch))
  HOP_GRID.forEach((row, r) => row.forEach(([a, b], i) => add(a, b, gx + i * cw, gy + ch * (r + 1), cw, ch)))
  add(HOP_ROW4.six[0], HOP_ROW4.six[1], gx + cw * 2, r4y, cw, ch)
  add(HOP_ROW4.eight[0], HOP_ROW4.eight[1], gx + cw * 3, r4y, cw, ch)

  return map
}

// Hardway number -> the PairCell's (a, col, row) as PropsPanel's own
// `hards` array defines them.
const HARDWAY_CELLS: Record<number, { a: number; col: 0 | 1; row: 0 | 1 }> = {
  6: { a: 3, col: 0, row: 0 },
  8: { a: 4, col: 1, row: 0 },
  4: { a: 2, col: 0, row: 1 },
  10: { a: 5, col: 1, row: 1 },
}

function hardwayZone(n: number): FeltZone | null {
  const cell = HARDWAY_CELLS[n]
  if (!cell) return null
  const gx2 = PROPS.x + 4
  const cellW = (PROPS.w - 8) / 2
  const cellH = 54
  const hardY = PROPS.y + 50
  const ox = cell.col === 1 ? 10 : 0
  const x = gx2 + cell.col * cellW
  const y = hardY + cell.row * cellH
  const ccx = x + cellW / 2 + ox
  const ccy = y + cellH / 2
  return { zoneId: `pair-${cell.a}-${cell.a}`, x: ccx - 26, y: ccy }
}

function hornZone(): FeltZone {
  const cellH = 54
  const hardY = PROPS.y + 50
  const hornY = hardY + cellH * 2 + 10
  return { zoneId: 'horn-bet', x: PROPS.x + PROPS.w / 2, y: hornY + cellH }
}

function anyCrapsZone(): FeltZone {
  const BAND_H = 38
  const y = PROPS.y + PROPS.h - (BAND_H + 6)
  return { zoneId: "band-Any Craps", x: PROPS.x + PROPS.w - 40, y: y + BAND_H / 2 }
}

// ATS bet-cell name (engine's "All"/"Tall"/"Small") -> felt cell name
// (AtsPanel's own `cells` array) -> (x, cw) via its cumulative-width
// cursor.
const ATS_NAME: Record<string, string> = { Small: 'All Small', All: "Make'Em All", Tall: 'All Tall' }

function atsZone(betType: 'All' | 'Tall' | 'Small'): FeltZone {
  const name = ATS_NAME[betType]
  const gx = ATS.x + 3
  const gy = ATS.y + 48
  const chh = ATS.h - 51
  const widths = [104, ATS.w - 6 - 208, 104]
  const order = ['All Small', "Make'Em All", 'All Tall']
  let x = gx
  for (const n of order) {
    const cw = widths[order.indexOf(n)]
    if (n === name) return { zoneId: `ats-${name}`, x: x + cw / 2, y: gy + chh - 18 }
    x += cw
  }
  throw new Error(`unreachable: unknown ATS name ${name}`)
}

const BOX_ZONES = boxZones()
const HOP_ZONES = hopZones()

/** Number in a "Place"/"Lay"/etc. position, or null if not a plain point number. */
function pointNumber(n: BetNumber): number | null {
  return typeof n === 'number' ? n : null
}

export function feltZoneFor(betType: string, number: BetNumber): FeltZone | null {
  switch (betType) {
    case 'Pass Line':
      return { zoneId: 'passline', x: 1080, y: 697 }
    case "Don't Pass":
      return { zoneId: 'dontpass', x: 1080, y: 645 }
    case 'Pass Line Odds':
    case "Don't Pass Odds":
      return { zoneId: 'passline-odds', x: PASSLINE_ODDS_FILL.x + 40, y: PASSLINE_ODDS_FILL.y + 8 }
    case 'Come': {
      const n = pointNumber(number)
      if (n === null) return { zoneId: 'come', x: COME.x + COME.w / 2, y: COME.y + COME.h - 26 }
      return BOX_ZONES.get(n)?.come ?? null
    }
    case 'Come Odds': {
      const n = pointNumber(number)
      return n === null ? null : (BOX_ZONES.get(n)?.comeOdds ?? null)
    }
    case "Don't Come": {
      const n = pointNumber(number)
      if (n === null) return { zoneId: 'dontcome', x: DC.x + DC.w / 2, y: DC.y + 140 }
      return BOX_ZONES.get(n)?.dontcome ?? null
    }
    case "Don't Come Odds": {
      const n = pointNumber(number)
      return n === null ? null : (BOX_ZONES.get(n)?.dontcomeOdds ?? null)
    }
    case "Don't Place": {
      const n = pointNumber(number)
      return n === null ? null : (BOX_ZONES.get(n)?.laydc ?? null)
    }
    case 'Field':
      return { zoneId: 'field', x: FIELD.x + FIELD.w / 2, y: FIELD.y + FIELD.h - 60 }
    case 'Place':
    case 'Buy': {
      const n = pointNumber(number)
      return n === null ? null : (BOX_ZONES.get(n)?.place ?? null)
    }
    case 'Lay': {
      const n = pointNumber(number)
      return n === null ? null : (BOX_ZONES.get(n)?.laydc ?? null)
    }
    case 'Hop': {
      if (!Array.isArray(number)) return null
      const [a, b] = number
      return HOP_ZONES.get(`${Math.min(a, b)}-${Math.max(a, b)}`) ?? null
    }
    case 'Hardways': {
      const n = pointNumber(number)
      return n === null ? null : hardwayZone(n)
    }
    case 'All':
    case 'Tall':
    case 'Small':
      return atsZone(betType)
    case 'Horn':
      return hornZone()
    case 'Any Craps':
      return anyCrapsZone()
    default:
      return null
  }
}
