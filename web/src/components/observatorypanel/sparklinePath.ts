/**
 * Turns a bankroll history into a normalized SVG polyline `points`
 * string for a tiny per-row sparkline. Hand-rolled rather than
 * recharts — at 80x12px there's no room for axes/tooltips/legends,
 * and mounting a full chart per roster row would be needless overhead
 * for a shape this simple.
 */
export function sparklinePoints(history: number[], width: number, height: number): string {
  if (history.length === 0) return ''
  if (history.length === 1) return `0,${height / 2} ${width},${height / 2}`

  const min = Math.min(...history)
  const max = Math.max(...history)
  const span = max - min

  return history
    .map((value, i) => {
      const x = (i / (history.length - 1)) * width
      const y = span === 0 ? height / 2 : height - ((value - min) / span) * height
      return `${x.toFixed(2)},${y.toFixed(2)}`
    })
    .join(' ')
}

/** Up if the last value is >= the first, down otherwise — drives the line's color. */
export function sparklineTrend(history: number[]): 'up' | 'down' {
  if (history.length < 2) return 'up'
  return history[history.length - 1] >= history[0] ? 'up' : 'down'
}
