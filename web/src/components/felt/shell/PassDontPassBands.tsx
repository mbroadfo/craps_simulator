import { FONT_DISPLAY, FONT_SCRIPT } from '../fonts'
import { DONTPASS_FILL_D, PASSLINE_ODDS_FILL, PASS_FILL_D } from '../layout'
import { BarTwelve } from '../panels/Dice'
import { useZone } from '../state/useZone'

/**
 * The Pass Line / Don't Pass wrap-around bands — static SVG path data,
 * ported verbatim (see layout.ts's own comment: never hand-retype
 * these coordinates). The prototype's on/off toggle for this band
 * (and every other Sections/Table toggle) was dropped rather than
 * wired up — see DevControlsPanel's own comment.
 */
export function PassDontPassBands() {
  const passZone = useZone('Pass Line — even money · edge 1.41%', 'passline', 1080, 697)
  const dontPassZone = useZone("Don't Pass Bar 12 — even money · edge 1.36%", 'dontpass', 1080, 645)
  const oddsZone = useZone('Pass Line Odds — true odds, 0% edge · behind the flat bet', 'passline-odds', 1100, 734)

  return (
    <>
      <path
        id="pass-fill"
        d={PASS_FILL_D}
        fill="#12301e"
        stroke="#c9a84c"
        strokeWidth={1.5}
        {...passZone}
      />
      <path
        id="dontpass-fill"
        d={DONTPASS_FILL_D}
        fill="#241019"
        stroke="#c9a84c"
        strokeWidth={1.5}
        {...dontPassZone}
      />
      {/* Pass Line odds have no printed felt zone on a real table — this
          is only a dev-tool click target, in the open margin below
          Pass Line's own printed edge. */}
      <rect
        id="passline-odds-fill"
        x={PASSLINE_ODDS_FILL.x}
        y={PASSLINE_ODDS_FILL.y}
        width={PASSLINE_ODDS_FILL.w}
        height={PASSLINE_ODDS_FILL.h}
        fill="transparent"
        pointerEvents="all"
        {...oddsZone}
      />
    </>
  )
}

/**
 * Pass Line / Don't Pass band text + dice (drawDpLabels in the
 * prototype) — a separate group (renders into the felt's own
 * <g id="dp-labels">, a sibling AFTER the rail-outline rects, see
 * Felt.tsx) because the prototype rebuilt this independently of the
 * static band fills.
 */
export function DpLabels() {
  return (
    // pointerEvents="none" — this group paints on top of pass-fill/
    // dontpass-fill (a sibling, not a descendant, of those paths), so
    // without this a click on the "Pass Line"/"Don't Pass"/"Bar" text
    // or its dice would be swallowed here instead of reaching the
    // band's own zone underneath. Purely decorative, so it should
    // never intercept a click meant for the shape it's labeling.
    <g data-testid="dp-labels-content" pointerEvents="none">
      {/* Pass Line — bottom strip and rotated right rail */}
      <text x={795} y={697} textAnchor="middle" dominantBaseline="middle" fill="url(#ember)" fontFamily={FONT_DISPLAY} fontStyle="italic" fontSize={30} fontWeight={700} letterSpacing={14}>
        Pass Line
      </text>
      <g transform="translate(1358,440) rotate(-90)">
        <text textAnchor="middle" dominantBaseline="middle" fill="url(#ember)" fontFamily={FONT_DISPLAY} fontStyle="italic" fontSize={24} fontWeight={700} letterSpacing={9}>
          Pass Line
        </text>
      </g>

      {/* The bet… */}
      <text x={680} y={645} textAnchor="middle" dominantBaseline="middle" fill="#d8cfae" fontFamily={FONT_DISPLAY} fontStyle="italic" fontSize={17} fontWeight={700} letterSpacing={4}>
        Don&apos;t Pass
      </text>
      {/* …and, well apart, the constraint */}
      <text x={915} y={645} textAnchor="middle" dominantBaseline="middle" fill="#d8cfae" fontFamily={FONT_SCRIPT} fontStyle="italic" fontSize={18}>
        Bar
      </text>
      <BarTwelve cx={970} cy={645} s={24} />

      <g transform="translate(1305,440) rotate(-90)">
        <text textAnchor="middle" dominantBaseline="central" fill="#d8cfae" fontFamily={FONT_DISPLAY} fontStyle="italic" fontSize={18} fontWeight={700} letterSpacing={3}>
          Don&apos;t Pass
        </text>
      </g>
      {/* Reading up the rail, Bar 12 continues AFTER Don't Pass (above it) */}
      <g transform="translate(1305,330) rotate(-90)">
        <text textAnchor="middle" dominantBaseline="middle" fill="#d8cfae" fontFamily={FONT_SCRIPT} fontStyle="italic" fontSize={16}>
          Bar
        </text>
      </g>
      {/* Dice stacked along the lane, rotated for the player standing table-right */}
      <g transform="translate(1305,290) rotate(-90)">
        <BarTwelve cx={0} cy={0} s={20} />
      </g>
    </g>
  )
}
