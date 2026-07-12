import { FONT_DISPLAY, FONT_SCRIPT } from '../fonts'
import { DC } from '../layout'
import { useFeltState } from '../state/FeltStateContext'
import { useZone } from '../state/useZone'
import { BarTwelve } from './Dice'
import { Puck } from './Puck'

/**
 * The Don't Come box (drawDontCome in the prototype), caps the top of
 * Don't Pass's lane.
 */
export function DontComeBox() {
  const { cfg } = useFeltState()
  const puck = cfg.puck
  const zone = useZone("DON'T COME — even money once behind a number · bar 12 · edge 1.36%", 'dontcome', DC.x + DC.w / 2, DC.y + 140)

  return (
    <g data-testid="dont-come">
      <rect x={DC.x} y={DC.y} width={DC.w} height={DC.h} rx={4} fill="#100e14" stroke="#d8cfae" strokeWidth={1.2} {...zone} />
      {/* pointerEvents="none" — this content paints on top of the
          zoned rect above (a sibling, not a descendant); without it a
          click on the puck/text/dice would be swallowed here instead
          of reaching the "dontcome" zone. */}
      <g pointerEvents="none">
        {puck === null && <Puck cx={DC.x + DC.w / 2} cy={DC.y + 46} r={22} on={false} />}
        <text
          x={DC.x + DC.w / 2}
          y={DC.y + 116}
          textAnchor="middle"
          fill="#d8cfae"
          fontFamily={FONT_DISPLAY}
          fontStyle="italic"
          fontSize={20}
          fontWeight={700}
          letterSpacing={1}
        >
          Don&apos;t
        </text>
        <text
          x={DC.x + DC.w / 2}
          y={DC.y + 144}
          textAnchor="middle"
          fill="#d8cfae"
          fontFamily={FONT_DISPLAY}
          fontStyle="italic"
          fontSize={20}
          fontWeight={700}
          letterSpacing={1}
        >
          Come
        </text>
        <text
          x={DC.x + DC.w / 2}
          y={DC.y + 194}
          textAnchor="middle"
          fill="#d8cfae"
          fontFamily={FONT_SCRIPT}
          fontStyle="italic"
          fontSize={19}
        >
          Bar
        </text>
        <BarTwelve cx={DC.x + DC.w / 2} cy={DC.y + 220} s={24} />
      </g>
    </g>
  )
}
