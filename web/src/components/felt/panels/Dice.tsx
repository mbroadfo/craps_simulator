const PIPS: Record<number, [number, number][]> = {
  1: [[0, 0]],
  2: [
    [-1, -1],
    [1, 1],
  ],
  3: [
    [-1, -1],
    [0, 0],
    [1, 1],
  ],
  4: [
    [-1, -1],
    [1, -1],
    [-1, 1],
    [1, 1],
  ],
  5: [
    [-1, -1],
    [1, -1],
    [0, 0],
    [-1, 1],
    [1, 1],
  ],
  6: [
    [-1, -1],
    [1, -1],
    [-1, 0],
    [1, 0],
    [-1, 1],
    [1, 1],
  ],
}

interface MiniDieProps {
  cx: number
  cy: number
  v: number
  s?: number
  face?: string
}

// A single die face — used everywhere a small dice icon appears (hop
// grid, hardways/Horn pair cells, Bar 12, the "The Pit" logo uses its
// own inline version). Shared because >=3 unrelated panels need it.
export function MiniDie({ cx, cy, v, s = 14, face = '#efe7d3' }: MiniDieProps) {
  const k = s / 3.9
  return (
    <g>
      <rect x={cx - s / 2} y={cy - s / 2} width={s} height={s} rx={2.5} fill={face} stroke="#20180f" strokeWidth={1} />
      {PIPS[v].map(([dx, dy], i) => (
        <circle key={i} cx={cx + dx * k} cy={cy + dy * k} r={s / 7.5} fill="#20180f" />
      ))}
    </g>
  )
}

// Two 6s side by side — the "Bar 12" indicator next to Don't Pass/Don't
// Come.
export function BarTwelve({ cx, cy, s }: { cx: number; cy: number; s: number }) {
  return (
    <g>
      <MiniDie cx={cx - (s / 2 + 2)} cy={cy} v={6} s={s} />
      <MiniDie cx={cx + (s / 2 + 2)} cy={cy} v={6} s={s} />
    </g>
  )
}
