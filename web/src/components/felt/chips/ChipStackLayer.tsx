import { DENOMS } from '../data'
import { FONT_MONO } from '../fonts'
import { useFeltState } from '../state/FeltStateContext'
import { ChipFace } from './ChipFace'

/**
 * Felt bet-stack rendering (drawChipLayer/chipToken in the prototype)
 * — reads placed chips from FeltStateContext. Largest denomination
 * sorts to the bottom of the stack; the topmost/most-visible chip
 * shows the bet's running $ total instead of its own face value, so
 * the total is readable without counting the stack. Only the top 5
 * chips render, with a "+N" overflow label beyond that.
 */
export function ChipStackLayer() {
  const { chips } = useFeltState()

  return (
    <g data-testid="chip-stack-layer">
      {Object.entries(chips).map(([id, zone]) => {
        if (!zone.denoms.length) return null
        const total = zone.denoms.reduce((sum, v) => sum + v, 0)
        const sorted = [...zone.denoms].sort((a, b) => b - a)
        const shown = Math.min(sorted.length, 5)
        const slice = sorted.slice(0, shown)
        const size = 60 // matches the denomination picker's chips

        return (
          <g key={id}>
            {slice.map((denomValue, i) => {
              const d = DENOMS.find((x) => x.value === denomValue) ?? DENOMS[0]
              const isTop = i === shown - 1
              const cy = zone.y - i * 7
              return <ChipFace key={i} d={d} size={size} x={zone.x - size / 2} y={cy - size / 2} labelOverride={isTop ? `$${total}` : undefined} />
            })}
            {zone.denoms.length > shown && (
              <text x={zone.x + 42} y={zone.y - (shown - 1) * 7 - 28} textAnchor="middle" fill="#f3ce74" fontFamily={FONT_MONO} fontSize={13} fontWeight={700}>
                +{zone.denoms.length - shown}
              </text>
            )}
          </g>
        )
      })}
    </g>
  )
}
