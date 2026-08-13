import { FELT_W } from '../layout'
import { useFeltState } from '../state/FeltStateContext'

/**
 * Win/loss/return toast layer (showBetToast in the prototype) —
 * dicer.io-style: white rounded card, colored border (green win / red
 * loss / neutral grey return), bold black "+$N"/"-$N"/"Returned",
 * fades up and out (.bet-toast in Felt.css). Real resolutions carry a
 * `kind` (see tableReducer.ts's BetResolved case); the dev-tool win/
 * loss test buttons don't, and fall back to deriving win/loss from
 * `amount`'s sign.
 */
export function BetToast() {
  const { toasts } = useFeltState()

  return (
    <g id="toast-layer">
      {toasts.map((t) => {
        const kind = t.kind ?? (t.amount >= 0 ? 'win' : 'loss')
        const label = kind === 'return' ? 'Returned' : `${kind === 'win' ? '+' : '-'}$${Math.abs(t.amount)}`
        const stroke = kind === 'win' ? '#2f8a5b' : kind === 'loss' ? '#c0392b' : '#8a8f98'
        const w = 44 + label.length * 13
        const h = 38
        const cx = Math.max(w / 2 + 4, Math.min(FELT_W - w / 2 - 4, t.x))
        const cy = Math.max(h / 2 + 4, t.y)
        return (
          // Position and animation are split across two <g>s on
          // purpose: .bet-toast's CSS @keyframes animates `transform`,
          // and a CSS transform animation on an element COMPLETELY
          // REPLACES its SVG transform= attribute rather than
          // combining with it — putting both on one <g> collapsed
          // every toast to the SVG origin (upper-left corner). The
          // outer <g> holds the real position as a plain attribute
          // (untouched by CSS); the inner <g> only carries the
          // animation, with no transform attribute of its own for the
          // animation to clobber.
          <g key={t.id} transform={`translate(${cx},${cy})`}>
            <g className="bet-toast">
              <rect
                x={-w / 2}
                y={-h / 2}
                width={w}
                height={h}
                rx={9}
                fill="#ffffff"
                stroke={stroke}
                strokeWidth={3}
                style={{ filter: 'drop-shadow(0 3px 5px rgba(0,0,0,0.6))' }}
              />
              <text x={0} y={7} textAnchor="middle" fill="#111111" fontFamily="Arial, Helvetica, sans-serif" fontWeight={800} fontSize={kind === 'return' ? 15 : 20}>
                {label}
              </text>
            </g>
          </g>
        )
      })}
    </g>
  )
}
