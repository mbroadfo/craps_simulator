import { DENOMS } from '../data'
import { useFeltState } from '../state/FeltStateContext'
import { useFeltScale } from '../state/useFeltScale'
import { ChipFace } from './ChipFace'

/**
 * Denomination picker (buildDenomPicker in the prototype) — single
 * chip per denomination (not a stack), so picking one is a deliberate,
 * obvious click, separate from clicking a chip group directly in the
 * rail (which also still works). Sized off the felt's own rendered
 * width (useFeltScale) rather than a fixed 60px, so it scales with
 * the table instead of staying a constant screen size — see
 * useFeltScale's own comment.
 */
export function DenomPicker() {
  const { selectedDenom, setSelectedDenom } = useFeltState()
  const scale = useFeltScale()
  const size = 60 * scale

  return (
    <div className="denomPicker" id="denomPicker" style={{ gap: 8 * scale }}>
      {DENOMS.map((d) => (
        <div
          key={d.value}
          className={'denomChip' + (d.value === selectedDenom ? ' selected' : '')}
          title={`$${d.value} — click to select as the active denomination`}
          onClick={() => setSelectedDenom(d.value)}
          style={{ width: size, height: size }}
        >
          <ChipFace d={d} size={size} />
        </div>
      ))}
    </div>
  )
}
