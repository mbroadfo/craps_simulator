/** A single white die face with black pips, 1-6. `null` renders a blank (unrolled) face rather than disappearing. */
const PIP_LAYOUTS: Record<number, [number, number][]> = {
  1: [[20, 20]],
  2: [[12, 12], [28, 28]],
  3: [[12, 12], [20, 20], [28, 28]],
  4: [[12, 12], [28, 12], [12, 28], [28, 28]],
  5: [[12, 12], [28, 12], [20, 20], [12, 28], [28, 28]],
  6: [[12, 10], [28, 10], [12, 20], [28, 20], [12, 30], [28, 30]],
}

export function DiceFace({ value }: { value: number | null }) {
  const pips = value !== null ? (PIP_LAYOUTS[value] ?? []) : []
  return (
    <svg width={40} height={40} viewBox="0 0 40 40" aria-hidden="true">
      <rect x={1} y={1} width={38} height={38} rx={7} fill="#ffffff" stroke="#c9a84c" strokeWidth={1.5} />
      {pips.map(([cx, cy], i) => (
        <circle key={i} cx={cx} cy={cy} r={3.4} fill="#14100a" />
      ))}
    </svg>
  )
}
