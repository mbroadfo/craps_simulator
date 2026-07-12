import type { Denom } from '../data'

/**
 * A poker-chip icon (chipFaceSVG in the prototype): body in the chip's
 * own casino color, a dashed edge-spot ring, a soft top sheen, and a
 * bold white numeral (dark outline so it stays legible even on the
 * pale $1 chip). Nested <svg> so it can be reused at any size — the
 * denom picker and the felt's own bet-stack chips (ChipStackLayer,
 * Step 2's interactivity step) share this one chip design.
 */
export function ChipFace({ d, size, labelOverride, x, y }: { d: Denom; size: number; labelOverride?: string; x?: number; y?: number }) {
  const label = labelOverride ?? `$${d.value}`
  const fontSize = label.length <= 2 ? 13 : label.length === 3 ? 11 : 9

  return (
    <svg x={x} y={y} width={size} height={size} viewBox="0 0 40 40">
      <circle cx={20} cy={20} r={19} fill={d.fill} stroke="#00000055" strokeWidth={1} />
      <circle cx={20} cy={20} r={16} fill="none" stroke={d.edge} strokeWidth={3} strokeDasharray="4 3.5" />
      <circle cx={20} cy={20} r={12.5} fill="none" stroke={d.edge} strokeWidth={1} strokeOpacity={0.6} />
      <ellipse cx={16} cy={13} rx={8.5} ry={4.5} fill="#ffffff" fillOpacity={0.22} />
      <text
        x={20}
        y={24.5}
        textAnchor="middle"
        fontFamily="Arial, Helvetica, sans-serif"
        fontWeight={800}
        fontSize={fontSize}
        fill="#ffffff"
        stroke="#00000090"
        strokeWidth={2}
        paintOrder="stroke fill"
      >
        {label}
      </text>
    </svg>
  )
}
