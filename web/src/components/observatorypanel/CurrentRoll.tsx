import { DiceFace } from './DiceFace'
import './ObservatoryPanel.css'
import { formatRollSum } from './rollSum'

/** A label, two dice faces, and the sum (hardways shown as e.g. "6H") — the most recent roll. Sits above the Bot roster. */
export function CurrentRoll({ dice }: { dice: [number, number] | null }) {
  return (
    <div className="obsCurrentRoll">
      <span className="obsCurrentRollLabel">Roll</span>
      <div className="obsCurrentRollDice">
        <DiceFace value={dice?.[0] ?? null} />
        <DiceFace value={dice?.[1] ?? null} />
      </div>
      <span className="obsCurrentRollSum">{formatRollSum(dice)}</span>
    </div>
  )
}
