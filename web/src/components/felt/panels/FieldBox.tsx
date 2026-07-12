import { FONT_DISPLAY, FONT_SCRIPT } from '../fonts'
import { FIELD } from '../layout'
import { useFeltState } from '../state/FeltStateContext'
import { useZone } from '../state/useZone'

// "PAYS DOUBLE/TRIPLE" arched under a field circle, hugging its rim.
// Single-use (only FieldBox calls it) — stays local per the plan.
function ArcLabel({ id, cx, cy, label }: { id: string; cx: number; cy: number; label: string }) {
  return (
    <>
      <path id={id} d={`M ${cx - 58},${cy + 26} A 62,62 0 0 0 ${cx + 58},${cy + 26}`} fill="none" />
      <text fill="#c9a84c" fontFamily={FONT_SCRIPT} fontStyle="italic" fontSize={15} fontWeight={700} letterSpacing={1} textAnchor="middle">
        <textPath href={`#${id}`} startOffset="50%">
          {label}
        </textPath>
      </text>
    </>
  )
}

// The Field bet (drawField in the prototype).
export function FieldBox() {
  const { cfg } = useFeltState()
  const field2 = cfg.field2
  const field12 = cfg.field12

  const leftCx = FIELD.x + 96
  const rightCx = FIELD.x + FIELD.w - 96
  const yAt = (t: number) => FIELD.y + 96 - 30 * Math.sin(Math.PI * t)
  const xAt = (t: number) => leftCx + t * (rightCx - leftCx)
  const mids = [3, 4, 9, 10, 11]
  const edge = (((6 - field2 - field12) / 36) * 100).toFixed(2)
  const zone = useZone(`FIELD — one roll · 3·4·9·10·11 even, 2 pays ${field2}×, 12 pays ${field12}× · edge ${edge}%`, 'field', FIELD.x + FIELD.w / 2, FIELD.y + FIELD.h - 60)

  return (
    <g data-testid="field-box">
      <rect x={FIELD.x} y={FIELD.y} width={FIELD.w} height={FIELD.h} rx={10} fill="#0c0d11" stroke="#c9a84c" strokeWidth={1.2} {...zone} />

      {/* pointerEvents="none" — everything below is decorative,
          painted on top of the zoned rect above; a click on any of it
          shouldn't be swallowed here instead of reaching "field". */}
      <g pointerEvents="none">
        <circle cx={leftCx} cy={yAt(0)} r={36} fill="none" stroke="#d8cfae" strokeWidth={field2 === 3 ? 2.2 : 1.4} />
        <text x={leftCx} y={yAt(0)} textAnchor="middle" dominantBaseline="middle" fill="url(#ember)" fontFamily={FONT_DISPLAY} fontStyle="italic" fontSize={52} fontWeight={900}>
          2
        </text>
        <ArcLabel id="field-arc-2" cx={leftCx} cy={yAt(0)} label={`Pays ${field2 === 3 ? 'Triple' : 'Double'}`} />

        <circle cx={rightCx} cy={yAt(1)} r={36} fill="none" stroke="#d8cfae" strokeWidth={field12 === 3 ? 2.2 : 1.4} />
        <text x={rightCx} y={yAt(1)} textAnchor="middle" dominantBaseline="middle" fill="url(#ember)" fontFamily={FONT_DISPLAY} fontStyle="italic" fontSize={46} fontWeight={900}>
          12
        </text>
        <ArcLabel id="field-arc-12" cx={rightCx} cy={yAt(1)} label={`Pays ${field12 === 3 ? 'Triple' : 'Double'}`} />

        {mids.map((n, i) => {
          const t = (i + 1) / 6
          const tm = (i + 1.5) / 6
          return (
            <g key={n}>
              <text x={xAt(t)} y={yAt(t)} textAnchor="middle" dominantBaseline="middle" fill="url(#ember)" fontFamily={FONT_DISPLAY} fontStyle="italic" fontSize={56} fontWeight={900}>
                {n}
              </text>
              {i < mids.length - 1 && (
                <text x={xAt(tm)} y={yAt(tm)} textAnchor="middle" dominantBaseline="middle" fill="#d8cfae" fontFamily={FONT_DISPLAY} fontStyle="italic" fontSize={40}>
                  &middot;
                </text>
              )}
            </g>
          )
        })}

        <text
          x={FIELD.x + FIELD.w / 2}
          y={FIELD.y + FIELD.h - 38}
          textAnchor="middle"
          fill="url(#ember)"
          fontFamily={FONT_DISPLAY}
          fontStyle="italic"
          fontSize={40}
          fontWeight={700}
          letterSpacing={22}
        >
          Field
        </text>
      </g>
    </g>
  )
}
