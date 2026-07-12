import { FONT_SCRIPT } from '../fonts'
import { COME } from '../layout'
import { useZone } from '../state/useZone'

// The Come band (drawCome in the prototype).
export function ComeBox() {
  const zone = useZone('COME — even money, travels to the rolled number · edge 1.41%', 'come', COME.x + COME.w / 2, COME.y + COME.h - 26)

  return (
    <g data-testid="come-box">
      <rect x={COME.x} y={COME.y} width={COME.w} height={COME.h} rx={10} fill="#0d1210" stroke="#c9a84c" strokeWidth={1.2} {...zone} />
      {/* pointerEvents="none" — sits on top of the zoned rect above; a
          click on the glyphs shouldn't be swallowed here. */}
      <text
        x={COME.x + COME.w / 2}
        y={COME.y + COME.h / 2 + 4}
        textAnchor="middle"
        dominantBaseline="middle"
        fill="#c8412f"
        fontFamily={FONT_SCRIPT}
        fontStyle="italic"
        fontSize={84}
        fontWeight={700}
        letterSpacing={8}
        pointerEvents="none"
      >
        Come
      </text>
    </g>
  )
}
