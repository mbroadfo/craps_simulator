import { FONT_DISPLAY, FONT_MONO } from '../fonts'
import { ATS, SMALL_NUMS, TALL_NUMS } from '../layout'
import { EDGE } from '../data'
import { useFeltState } from '../state/FeltStateContext'
import { useZone } from '../state/useZone'

// One ATS tracker circle — its own component because it needs its own
// useZone() call (hooks can't be called inside a loop callback).
// Click toggles cfg.atsLit directly (separate from the chip-placement
// zone() mechanic — this is a hit/not-hit marker, not a bet).
function AtsTracker({ v, cx, cy }: { v: number; cx: number; cy: number }) {
  const { cfg, toggleAtsLit } = useFeltState()
  const lit = cfg.atsLit[v]
  const zone = useZone(`ATS tracker — ${v} ${lit ? 'hit' : 'not hit'} this shooter (click to toggle)`)

  return (
    <g onClick={() => toggleAtsLit(v)} {...zone}>
      <circle cx={cx} cy={cy} r={15} fill={lit ? '#4caf7d' : '#0f0f0f'} stroke={lit ? '#7fd6a4' : '#7a6a40'} strokeWidth={2} cursor="pointer" />
      <text x={cx} y={cy + 0.5} textAnchor="middle" dominantBaseline="middle" fill={lit ? '#0a2f1c' : '#7a6a40'} fontFamily={FONT_DISPLAY} fontStyle="italic" fontSize={lit ? 18 : 17} fontWeight={700} pointerEvents="none">
        {v}
      </text>
    </g>
  )
}

// All Small / Make'Em All / All Tall bet cell — its own component for
// its own useZone() call.
function AtsCell({ name, nums, pays, edge, x, cw, gy, chh, big }: { name: string; nums: string; pays: string; edge: string; x: number; cw: number; gy: number; chh: number; big: boolean }) {
  const zone = useZone(`${name} — ${pays} · edge ${edge} · every number (${nums}) must hit before a 7`, `ats-${name}`, x + cw / 2, gy + chh - 18)

  return (
    <g>
      <rect x={x} y={gy} width={cw} height={chh} fill="#0c0d11" stroke="#c9a84c" strokeWidth={0.8} {...zone} />
      <g pointerEvents="none">
        <text x={x + cw / 2} y={gy + 22} textAnchor="middle" fill="#e8a04a" fontFamily={FONT_DISPLAY} fontStyle="italic" fontSize={big ? 16 : 13} fontWeight={700} letterSpacing={1}>
          {name}
        </text>
        <text x={x + cw / 2} y={gy + 40} textAnchor="middle" fill="#a08d5f" fontFamily={FONT_MONO} fontStyle="italic" fontSize={nums.length > 12 ? 13 : 14}>
          {nums}
        </text>
        <text x={x + cw / 2} y={gy + 68} textAnchor="middle" fill="url(#ember-soft)" fontFamily={FONT_DISPLAY} fontStyle="italic" fontSize={big ? 22 : 18} fontWeight={700}>
          {pays}
        </text>
      </g>
    </g>
  )
}

/**
 * All Small / Tall / Make'Em All (drawAts in the prototype). Tracker
 * toggle and bet-cell chip placement are wired.
 */
export function AtsPanel() {
  const slots: (number | '/')[] = [...SMALL_NUMS, '/', ...TALL_NUMS]
  const step = (ATS.w - 20) / slots.length
  const trackY = ATS.y + 20

  const cells: [string, string, string, string][] = [
    ['All Small', '2·3·4·5·6', '34:1', EDGE.atsTS],
    ["Make'Em All", '2·3·4·5·6·8·9·10·11·12', '175:1', EDGE.atsAll],
    ['All Tall', '8·9·10·11·12', '34:1', EDGE.atsTS],
  ]
  const gx = ATS.x + 3
  const gy = ATS.y + 48
  const chh = ATS.h - 51
  const widths = [104, ATS.w - 6 - 208, 104]
  let xCursor = gx

  return (
    <g data-testid="ats-panel">
      <rect x={ATS.x} y={ATS.y} width={ATS.w} height={ATS.h} rx={6} fill="#0c0d11" />

      {slots.map((v, i) => {
        const cx = ATS.x + 10 + step * (i + 0.5)
        if (v === '/') {
          return (
            <text key="slash" x={cx} y={trackY + 1} textAnchor="middle" dominantBaseline="middle" fill="#c9a84c" fontFamily={FONT_DISPLAY} fontStyle="italic" fontSize={22} fontWeight={700}>
              /
            </text>
          )
        }
        return <AtsTracker key={v} v={v} cx={cx} cy={trackY} />
      })}

      {cells.map(([name, nums, pays, edge], i) => {
        const x = xCursor
        const cw = widths[i]
        xCursor += cw
        return <AtsCell key={name} name={name} nums={nums} pays={pays} edge={edge} x={x} cw={cw} gy={gy} chh={chh} big={i === 1} />
      })}
    </g>
  )
}
