import { FONT_DISPLAY } from '../fonts'

interface PuckProps {
  cx: number
  cy: number
  r: number
  on: boolean
}

// The craps "puck" — flat circle, no gradients/shadows/gold. Off:
// black fill, white border/text. On: white fill, black border/text.
// Shared by BoxNumbers (on-state, sits on a point number) and
// DontComeBox (off-state, sits on Don't Come when no point is up).
export function Puck({ cx, cy, r, on }: PuckProps) {
  return (
    <g transform={`translate(${cx},${cy})`} data-testid="puck">
      <circle cx={0} cy={0} r={r} fill={on ? '#f0f0f0' : '#111111'} stroke={on ? '#000000' : '#ffffff'} strokeWidth={1.5} />
      <text x={0} y={1} textAnchor="middle" dominantBaseline="middle" fill={on ? '#000000' : '#ffffff'} fontFamily={FONT_DISPLAY} fontStyle="italic" fontWeight={700} fontSize={r * 0.6}>
        {on ? 'ON' : 'OFF'}
      </text>
    </g>
  )
}
