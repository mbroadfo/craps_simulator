import { FONT_SCRIPT } from '../fonts'
import { HOPS, HOP_GRID, HOP_ROW4, HOP_SEVEN, type HopKind } from '../layout'
import { EDGE, HOP_FACE, HOP_STYLE } from '../data'
import { useZone } from '../state/useZone'
import { MiniDie } from './Dice'

// A single hop-bet cell — a pair of dice + payout, color-coded by
// kind (amber hard, bone easy, red hop-the-7). Single-use (only
// HopsPanel calls it), so it stays local per the plan.
function HopCell({ x, y, w, h, a, b, kind }: { x: number; y: number; w: number; h: number; a: number; b: number; kind: HopKind }) {
  const st = HOP_STYLE[kind]
  const s = 24 // uniform: hop-7 pairs match the hardway pairs below
  const dieY = y + h / 2 - 10
  const desc = kind === 'hard' ? 'hard' : kind === 'seven' ? 'hop the 7' : 'easy'
  const zone = useZone(`HOP ${a}-${b} (${desc}) — one roll · ${st.pays} · edge ${kind === 'hard' ? EDGE.hopHard : EDGE.hopEasy}`, `hop-${a}-${b}`, x + w / 2, y + h / 2 - 10)

  return (
    <g data-testid={`hop-${a}-${b}`}>
      <rect x={x} y={y} width={w} height={h} rx={3} fill="#0c0d11" stroke="#8a8171" strokeWidth={0.8} {...zone} />
      <g pointerEvents="none">
        <MiniDie cx={x + w / 2 - (s / 2 + 2)} cy={dieY} v={a} s={s} face={HOP_FACE[kind]} />
        <MiniDie cx={x + w / 2 + (s / 2 + 2)} cy={dieY} v={b} s={s} face={HOP_FACE[kind]} />
        <text x={x + w / 2} y={y + h / 2 + 19} textAnchor="middle" fill={st.payFill} fontFamily={FONT_SCRIPT} fontStyle="italic" fontSize={14} fontWeight={700}>
          {st.pays}
        </text>
      </g>
    </g>
  )
}

function LabelCell({ x, y, w, h, label }: { x: number; y: number; w: number; h: number; label: string }) {
  return (
    <g>
      <rect x={x} y={y} width={w} height={h} rx={3} fill="#0c0d11" stroke="#8a8171" strokeWidth={0.8} />
      <text x={x + w / 2} y={y + h / 2 + 1} textAnchor="middle" dominantBaseline="middle" fill="url(#ember)" fontFamily={FONT_SCRIPT} fontStyle="italic" fontSize={22} fontWeight={700}>
        {label}
      </text>
    </g>
  )
}

/**
 * The hop-bet grid (drawHops in the prototype) — a connected 6-column
 * grid, no title bar; row 1's red tint identifies hop-the-7 on its
 * own.
 */
export function HopsPanel() {
  const gx = HOPS.x + 3
  const gy = HOPS.y + 3
  const cw = (HOPS.w - 6) / 6
  const ch = (HOPS.h - 6) / 4
  const r4y = gy + ch * 3
  const frameZone = useZone('HOP BETS — hardways 30:1 (amber), easy ways 15:1, hop the 7 in red · one roll')

  return (
    <g data-testid="hops-panel">
      <rect x={HOPS.x} y={HOPS.y} width={HOPS.w} height={HOPS.h} rx={6} fill="#0c0d11" {...frameZone} />

      {/* ROW 1 — hop the 7: three merged cells of two columns each */}
      {HOP_SEVEN.map(([a, b], i) => (
        <HopCell key={`seven-${a}-${b}`} x={gx + i * cw * 2} y={gy} w={cw * 2} h={ch} a={a} b={b} kind="seven" />
      ))}

      {/* ROWS 2-3 — one combo per point-number column (4 5 6 8 9 10) */}
      {HOP_GRID.map((row, r) =>
        row.map(([a, b, kind], i) => <HopCell key={`${r}-${a}-${b}`} x={gx + i * cw} y={gy + ch * (r + 1)} w={cw} h={ch} a={a} b={b} kind={kind} />),
      )}

      {/* ROW 4 — corners merged into HOP / BET, 6 and 8 third combos centered */}
      <LabelCell x={gx} y={r4y} w={cw * 2} h={ch} label="Hop" />
      <HopCell x={gx + cw * 2} y={r4y} w={cw} h={ch} a={HOP_ROW4.six[0]} b={HOP_ROW4.six[1]} kind="easy" />
      <HopCell x={gx + cw * 3} y={r4y} w={cw} h={ch} a={HOP_ROW4.eight[0]} b={HOP_ROW4.eight[1]} kind="easy" />
      <LabelCell x={gx + cw * 4} y={r4y} w={cw * 2} h={ch} label="Bet" />
    </g>
  )
}
