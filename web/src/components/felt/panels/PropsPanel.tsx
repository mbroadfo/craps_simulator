import { FONT_DISPLAY, FONT_MONO, FONT_SCRIPT } from '../fonts'
import { PROPS } from '../layout'
import { EDGE } from '../data'
import { useZone } from '../state/useZone'
import { MiniDie } from './Dice'

// Single-line prop band: NAME + payout mirrored on both sides. Red,
// not ember — both bands are one-roll bets, same accent as Hop-the-7
// and Horn. Single-use (only PropsPanel calls it), stays local.
function Band({ y, name, pays, cx, info }: { y: number; name: string; pays: string; cx: number; info: string }) {
  const BAND_H = 38
  const midY = y + BAND_H / 2
  const zone = useZone(info, `band-${name}`, PROPS.x + PROPS.w - 40, midY)
  return (
    <g data-testid={`prop-band-${name}`}>
      <rect x={PROPS.x + 4} y={y} width={PROPS.w - 8} height={BAND_H} rx={4} fill="#111214" stroke="#c9a84c" strokeWidth={0.6} strokeOpacity={0.5} {...zone} />
      <g pointerEvents="none">
        <text x={cx - 68} y={midY} textAnchor="end" dominantBaseline="middle" fill="#d95f4c" fontFamily={FONT_MONO} fontStyle="italic" fontSize={18} fontWeight={700}>
          {pays}
        </text>
        <text x={cx} y={midY} textAnchor="middle" dominantBaseline="middle" fill="#d95f4c" fontFamily={FONT_DISPLAY} fontStyle="italic" fontSize={18} fontWeight={700} letterSpacing={1.5}>
          {name}
        </text>
        <text x={cx + 68} y={midY} textAnchor="start" dominantBaseline="middle" fill="#d95f4c" fontFamily={FONT_MONO} fontStyle="italic" fontSize={18} fontWeight={700}>
          {pays}
        </text>
      </g>
    </g>
  )
}

// A dice-pair + payout cell — shared shape for the hardways 2x2 and
// the Horn 2x2 beneath it. Single-use (only PropsPanel calls it).
function PairCell({
  x,
  y,
  cellW,
  cellH,
  a,
  b,
  pays,
  face,
  payFill,
  testId,
  info,
  ox = 0,
}: {
  x: number
  y: number
  cellW: number
  cellH: number
  a: number
  b: number
  pays: string
  face: string
  payFill: string
  testId: string
  info: string
  ox?: number
}) {
  const ccx = x + cellW / 2 + ox
  const ccy = y + cellH / 2
  const zone = useZone(info, `pair-${a}-${b}`, ccx - 26, ccy)
  return (
    <g data-testid={testId}>
      <rect x={x} y={y} width={cellW} height={cellH} rx={3} fill="#0c0d11" stroke="#c9a84c" strokeWidth={1} strokeOpacity={0.8} {...zone} />
      {/* 28px dice — larger than the hop grid; the Horn square still
          reads as the focal point because of its own size/border. */}
      <g pointerEvents="none">
        <MiniDie cx={ccx - 41} cy={ccy} v={a} s={28} face={face} />
        <MiniDie cx={ccx - 11} cy={ccy} v={b} s={28} face={face} />
        <text x={ccx + 12} y={ccy} textAnchor="start" dominantBaseline="middle" fill={payFill} fontFamily={FONT_MONO} fontStyle="italic" fontSize={15} fontWeight={700}>
          {pays}
        </text>
      </g>
    </g>
  )
}

/**
 * Big Red / Any Craps bands + Hardways/Horn grid + Horn Bet placard
 * (drawProps in the prototype).
 */
export function PropsPanel() {
  const cx = PROPS.x + PROPS.w / 2
  const BAND_H = 38
  const gx2 = PROPS.x + 4
  const gw = PROPS.w - 8
  const cellW = gw / 2
  const cellH = 54

  const hardY = PROPS.y + 50
  const hards: [number, string, number, number, string, string][] = [
    [3, '9:1', 0, 0, 'HARD 6', EDGE.hard68],
    [4, '9:1', 1, 0, 'HARD 8', EDGE.hard68],
    [2, '7:1', 0, 1, 'HARD 4', EDGE.hard410],
    [5, '7:1', 1, 1, 'HARD 10', EDGE.hard410],
  ]

  const hornY = hardY + cellH * 2 + 10
  const horns: [number, number, string, number, number][] = [
    [1, 1, '30:1', 0, 0],
    [1, 2, '15:1', 1, 0],
    [5, 6, '15:1', 0, 1],
    [6, 6, '30:1', 1, 1],
  ]
  const hornInfo = `HORN — 4-way split, $4 units · 2/12 pays 30:1, 3/11 pays 15:1 · edge ${EDGE.horn}`
  const hornBoxZone = useZone(`HORN — the whole 4-way bet, $4 units · edge ${EDGE.horn}`, 'horn-bet', cx, hornY + cellH)

  return (
    <g data-testid="props-panel">
      <rect x={PROPS.x} y={PROPS.y} width={PROPS.w} height={PROPS.h} rx={6} fill="#0c0d11" />

      <Band y={PROPS.y + 2} name="Big Red" pays="4:1" cx={cx} info={`Big Red (Any Seven) — one roll · 4:1 · edge ${EDGE.anySeven} (worst bet on the felt)`} />
      <Band y={PROPS.y + PROPS.h - (BAND_H + 6)} name="Any Craps" pays="7:1" cx={cx} info={`Any Craps — 2·3·12, one roll · 7:1 · edge ${EDGE.anyCraps}`} />

      {/* Hardways 2x2 — right column shifts right ~10px: the shared
          per-cell offset formula (dice left, payout trailing right)
          leaves a bigger outer margin on the right than the left has
          otherwise — this equalizes them. */}
      {hards.map(([a, pays, col, row, name, edge]) => (
        <PairCell
          key={name}
          x={gx2 + col * cellW}
          y={hardY + row * cellH}
          cellW={cellW}
          cellH={cellH}
          a={a}
          b={a}
          pays={pays}
          face="#e8a04a"
          payFill="#e8a04a"
          testId={`prop-${name}`}
          info={`${name} (${a}-${a}) — pays ${pays} · edge ${edge} · loses on easy ${a + a} or 7`}
          ox={col === 1 ? 10 : 0}
        />
      ))}

      {/* Horn 2x2 beneath, with the Horn square overlaying its center —
          dice stay centered in their cells, same as the hardways grid;
          the Horn Bet square below deliberately overlays the seam, not
          the dice. */}
      {horns.map(([a, b, pays, col, row]) => (
        <PairCell
          key={`horn-${a}-${b}`}
          x={gx2 + col * cellW}
          y={hornY + row * cellH}
          cellW={cellW}
          cellH={cellH}
          a={a}
          b={b}
          pays={pays}
          face="#d95f4c"
          payFill="#d95f4c"
          testId={`prop-horn-${a}-${b}`}
          info={hornInfo}
          ox={col === 1 ? 10 : 0}
        />
      ))}

      {/* Taller and narrower, "Horn" over "Bet" — reads as a placard
          sitting atop the grid rather than a wide label bar. On a real
          table this placard IS where the chip goes for a whole Horn
          bet — the four pair cells above are the paytable, not
          individual click targets. */}
      <rect x={cx - 33} y={hornY + cellH - 26} width={66} height={52} rx={6} fill="#0d1a0d" stroke="#c9a84c" strokeWidth={1.2} strokeOpacity={0.9} {...hornBoxZone} />
      <g pointerEvents="none">
        <text x={cx} y={hornY + cellH - 8} textAnchor="middle" dominantBaseline="middle" fill="#d95f4c" fontFamily={FONT_SCRIPT} fontStyle="italic" fontSize={18} fontWeight={700}>
          Horn
        </text>
        <text x={cx} y={hornY + cellH + 14} textAnchor="middle" dominantBaseline="middle" fill="#d95f4c" fontFamily={FONT_SCRIPT} fontStyle="italic" fontSize={18} fontWeight={700}>
          Bet
        </text>
      </g>
    </g>
  )
}
