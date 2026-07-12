import { describe, expect, it } from 'vitest'
import { computeSidebarScale } from './useSidebarAutoFit'

describe('computeSidebarScale', () => {
  it('shrinks when content is taller than available space', () => {
    expect(computeSidebarScale(100, 200)).toBe(0.5)
  })

  it('never scales up past 1:1 when content is shorter than available space', () => {
    // This is the documented past bug: an earlier version returned
    // availH/naturalH unconditionally, magnifying text once enough
    // sections were collapsed and blowing it out past the sidebar's
    // fixed width.
    expect(computeSidebarScale(500, 100)).toBe(1)
  })

  it('returns exactly 1:1 when content exactly fills the available space', () => {
    expect(computeSidebarScale(150, 150)).toBe(1)
  })

  it('does not divide by zero or return NaN when natural height is 0 (e.g. jsdom, unmeasured layout)', () => {
    expect(computeSidebarScale(0, 0)).toBe(1)
    expect(computeSidebarScale(-14, 0)).toBe(1)
  })
})
