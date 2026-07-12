import { BOX, BOX_WORD } from '../layout'
import { FONT_DISPLAY, FONT_SCRIPT } from '../fonts'
import { EDGE } from '../data'
import { useFeltState } from '../state/FeltStateContext'
import { useZone } from '../state/useZone'
import { Puck } from './Puck'

/**
 * One box-number cell — its own component (not inlined in BoxNumbers'
 * .map()) because each cell needs its own useZone() calls, and hooks
 * can't be called inside a loop callback (react-hooks/rules-of-hooks).
 */
function BoxCell({ n, x, puck }: { n: number; x: number; puck: number | null }) {
  const topH = 42
  const botH = 42
  const y1 = BOX.y + topH
  const y2 = BOX.y + BOX.h - botH
  const word = BOX_WORD[n]
  const midY = BOX.y + topH + (BOX.h - topH - botH) / 2 + 2
  const label = word || String(n)
  const buyable = [4, 5, 9, 10].includes(n)

  const outerZone = useZone(`${label.toUpperCase()} — top: place/buy · center: come point + odds · bottom: lay/don't-come`)
  const placeInfo =
    `PLACE ${label.toUpperCase()} — pays ${n === 6 || n === 8 ? '7:6' : n === 5 || n === 9 ? '7:5' : '9:5'} (edge ${EDGE.place[n]})` +
    (buyable ? ` · or BUY at true odds −5% vig (edge ${EDGE.buy_on_win[n]})` : '')
  const placeZone = useZone(placeInfo, `place-${n}`, x + BOX.w / 2, y2 + botH / 2)
  const layInfo = `LAY / DON'T COME ${label.toUpperCase()} — click to test chip placement`
  const layZone = useZone(layInfo, `laydc-${n}`, x + BOX.w / 2, BOX.y + topH / 2)

  return (
    <g data-testid={`box-${n}`}>
      <rect x={x} y={BOX.y} width={BOX.w} height={BOX.h} rx={4} fill="#0c0d11" stroke="#c9a84c" strokeWidth={1.4} {...outerZone} />
      {/* pointerEvents="none" — these paint on top of the outer zone
          above (siblings, not descendants); without it, hovering the
          numeral/lines in the middle "come point" strip wouldn't reach
          outerZone's hover info. */}
      <g pointerEvents="none">
        <line x1={x} y1={y1} x2={x + BOX.w} y2={y1} stroke="#c9a84c" strokeWidth={1.4} strokeOpacity={0.75} />
        <line x1={x} y1={y2} x2={x + BOX.w} y2={y2} stroke="#c9a84c" strokeWidth={1.4} strokeOpacity={0.75} />

        {/* Georgia italic has a higher optical center than Playfair
            digits; +8px drops Six/Nine onto the numerals' visual
            baseline. */}
        {word ? (
          <text x={x + BOX.w / 2} y={midY + 8} textAnchor="middle" dominantBaseline="middle" fill="url(#ember)" fontFamily={FONT_SCRIPT} fontStyle="italic" fontSize={56} fontWeight={700}>
            {word}
          </text>
        ) : (
          <text x={x + BOX.w / 2} y={midY} textAnchor="middle" dominantBaseline="middle" fill="url(#ember)" fontFamily={FONT_DISPLAY} fontStyle="italic" fontSize={96} fontWeight={700}>
            {n}
          </text>
        )}

        {puck === n && (
          // Centered on the line between the Lay/Don't Come strip and
          // the come-point area — not tucked in a corner.
          <Puck cx={x + BOX.w / 2} cy={y1} r={27} on />
        )}
      </g>

      <rect data-testid={`place-${n}`} x={x} y={y2} width={BOX.w} height={botH} fill="transparent" {...placeZone} />
      <rect data-testid={`laydc-${n}`} x={x} y={BOX.y} width={BOX.w} height={topH} fill="transparent" {...layZone} />
    </g>
  )
}

/**
 * The 4/5/6/8/9/10 box-number cells (drawBoxes in the prototype).
 * cfg.labels captions (off by default in the prototype too) were
 * never wired — not part of what the dev-controls panel exposes.
 */
export function BoxNumbers() {
  const { cfg } = useFeltState()
  const puck = cfg.puck

  return (
    <>
      {BOX.nums.map((n, i) => (
        <BoxCell key={n} n={n} x={BOX.x0 + i * (BOX.w + BOX.gap)} puck={puck} />
      ))}
    </>
  )
}
