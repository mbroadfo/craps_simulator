import { describe, expect, it } from 'vitest'
import { sparklinePoints, sparklineTrend } from './sparklinePath'

describe('sparklinePoints', () => {
  it('returns empty string for no history', () => {
    expect(sparklinePoints([], 80, 12)).toBe('')
  })

  it('centers a flat line for a single point', () => {
    expect(sparklinePoints([100], 80, 12)).toBe('0,6 80,6')
  })

  it('maps min/max to the full height, flipped (SVG y grows downward)', () => {
    const points = sparklinePoints([100, 200], 80, 12)
    expect(points).toBe('0.00,12.00 80.00,0.00')
  })

  it('centers every point when history is flat but has multiple values', () => {
    const points = sparklinePoints([50, 50, 50], 80, 12)
    expect(points).toBe('0.00,6.00 40.00,6.00 80.00,6.00')
  })
})

describe('sparklineTrend', () => {
  it('is up when the series ends at or above where it started', () => {
    expect(sparklineTrend([100, 90, 110])).toBe('up')
    expect(sparklineTrend([100, 100])).toBe('up')
  })

  it('is down when the series ends below where it started', () => {
    expect(sparklineTrend([100, 150, 80])).toBe('down')
  })

  it('is up for a single point or empty history (no trend to show)', () => {
    expect(sparklineTrend([100])).toBe('up')
    expect(sparklineTrend([])).toBe('up')
  })
})
