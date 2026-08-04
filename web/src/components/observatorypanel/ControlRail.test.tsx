// @vitest-environment jsdom
import '@testing-library/jest-dom/vitest'
import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import type { ComponentProps } from 'react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { FeltStateProvider } from '../felt/state/FeltStateContext'
import { ControlRail, MAX_SPEED } from './ControlRail'

afterEach(() => {
  cleanup()
})

// FeltStateProvider (no `value`) falls back to useFeltDevState — fine
// here, ControlRail only reads statsOpen/toggleStats off it, and the
// stats toggle is otherwise unrelated to table/game state.
function renderRail(overrides: Partial<ComponentProps<typeof ControlRail>> = {}) {
  const onStart = vi.fn()
  const onPauseResume = vi.fn()
  const onStep = vi.fn()
  const onReset = vi.fn()
  const onSpeedChange = vi.fn()

  const props: ComponentProps<typeof ControlRail> = {
    hasTable: false,
    canStart: true,
    creating: false,
    error: null,
    onStart,
    sessionState: null,
    onPauseResume,
    onStep,
    onReset,
    speed: 1,
    onSpeedChange,
    ...overrides,
  }

  const utils = render(
    <FeltStateProvider>
      <ControlRail {...props} />
    </FeltStateProvider>,
  )
  return { ...utils, onStart, onPauseResume, onStep, onReset, onSpeedChange }
}

describe('ControlRail — Start/Roll (primary button)', () => {
  it('before a table exists: reads Start, calls onStart, disabled while creating', () => {
    const { onStart } = renderRail({ hasTable: false, creating: false, canStart: true })
    const btn = screen.getByTitle('Start')
    expect(btn).not.toBeDisabled()
    fireEvent.click(btn)
    expect(onStart).toHaveBeenCalledTimes(1)
  })

  it('before a table exists: disabled while creating or when the lineup cannot start', () => {
    renderRail({ hasTable: false, creating: true })
    expect(screen.getByTitle('Start')).toBeDisabled()
    cleanup()
    renderRail({ hasTable: false, creating: false, canStart: false })
    expect(screen.getByTitle('Start')).toBeDisabled()
  })

  it('once a table exists and is paused: becomes Roll, enabled, calls onStep (not onStart)', () => {
    const { onStep, onStart } = renderRail({ hasTable: true, sessionState: 'paused' })
    const btn = screen.getByTitle('Roll — advance one roll, then stay paused')
    expect(btn).not.toBeDisabled()
    fireEvent.click(btn)
    expect(onStep).toHaveBeenCalledTimes(1)
    expect(onStart).not.toHaveBeenCalled()
  })

  it('disabled while auto-rolling (running) — cannot manually step during autoplay', () => {
    renderRail({ hasTable: true, sessionState: 'running' })
    expect(screen.getByTitle('Roll — advance one roll, then stay paused')).toBeDisabled()
  })

  it('disabled once the table has finished', () => {
    renderRail({ hasTable: true, sessionState: 'finished' })
    expect(screen.getByTitle('Roll — advance one roll, then stay paused')).toBeDisabled()
  })
})

describe('ControlRail — Autoplay', () => {
  it('disabled before a table exists', () => {
    renderRail({ hasTable: false })
    expect(screen.getByTitle('Autoplay — roll continuously')).toBeDisabled()
  })

  it('disabled once finished', () => {
    // finished is never running, so the title is always the idle one here
    renderRail({ hasTable: true, sessionState: 'finished' })
    expect(screen.getByTitle('Autoplay — roll continuously')).toBeDisabled()
  })

  it('idle (paused/not running): enabled, calls onPauseResume, not styled active', () => {
    const { onPauseResume } = renderRail({ hasTable: true, sessionState: 'paused' })
    const btn = screen.getByTitle('Autoplay — roll continuously')
    expect(btn).not.toBeDisabled()
    expect(btn.className).not.toContain('active')
    fireEvent.click(btn)
    expect(onPauseResume).toHaveBeenCalledTimes(1)
  })

  it('running: styled active, shows the pause glyph, still calls onPauseResume to stop it', () => {
    const { onPauseResume } = renderRail({ hasTable: true, sessionState: 'running' })
    const btn = screen.getByTitle('Pause — stop auto-rolling')
    expect(btn.className).toContain('active')
    expect(btn.textContent).toContain('⏸')
    fireEvent.click(btn)
    expect(onPauseResume).toHaveBeenCalledTimes(1)
  })
})

describe('ControlRail — Turbo', () => {
  it('below max speed: clicking jumps to MAX_SPEED', () => {
    const { onSpeedChange } = renderRail({ hasTable: true, sessionState: 'paused', speed: 1 })
    fireEvent.click(screen.getByTitle('Turbo — jump to max speed'))
    expect(onSpeedChange).toHaveBeenCalledWith(MAX_SPEED)
  })

  it('already at max speed: clicking drops back to 1x', () => {
    const { onSpeedChange } = renderRail({ hasTable: true, sessionState: 'paused', speed: MAX_SPEED })
    fireEvent.click(screen.getByTitle('Turbo — jump to max speed'))
    expect(onSpeedChange).toHaveBeenCalledWith(1)
  })

  it('styled active only once speed reaches MAX_SPEED', () => {
    renderRail({ hasTable: true, sessionState: 'paused', speed: 1 })
    expect(screen.getByTitle('Turbo — jump to max speed').className).not.toContain('active')
    cleanup()
    renderRail({ hasTable: true, sessionState: 'paused', speed: MAX_SPEED })
    expect(screen.getByTitle('Turbo — jump to max speed').className).toContain('active')
  })

  it('disabled before a table exists or once finished', () => {
    renderRail({ hasTable: false })
    expect(screen.getByTitle('Turbo — jump to max speed')).toBeDisabled()
    cleanup()
    renderRail({ hasTable: true, sessionState: 'finished' })
    expect(screen.getByTitle('Turbo — jump to max speed')).toBeDisabled()
  })
})

describe('ControlRail — speed slider', () => {
  it('calls onSpeedChange with the numeric value on change', () => {
    const { onSpeedChange, container } = renderRail({ hasTable: true, sessionState: 'paused', speed: 1 })
    const slider = container.querySelector('.railSlider') as HTMLInputElement
    fireEvent.change(slider, { target: { value: '4.5' } })
    expect(onSpeedChange).toHaveBeenCalledWith(4.5)
  })

  it('disabled before a table exists', () => {
    const { container } = renderRail({ hasTable: false })
    expect(container.querySelector('.railSlider')).toBeDisabled()
  })
})

describe('ControlRail — Reset', () => {
  it('disabled before a table exists', () => {
    renderRail({ hasTable: false })
    expect(screen.getByTitle('Reset — end this game and start a new one')).toBeDisabled()
  })

  it('enabled once a table exists, calls onReset', () => {
    const { onReset } = renderRail({ hasTable: true, sessionState: 'finished' })
    const btn = screen.getByTitle('Reset — end this game and start a new one')
    expect(btn).not.toBeDisabled()
    fireEvent.click(btn)
    expect(onReset).toHaveBeenCalledTimes(1)
  })
})

describe('ControlRail — stats toggle', () => {
  it('calls toggleStats and flips aria-pressed on click', () => {
    renderRail()
    const btn = screen.getByTitle('Toggle stats panel')
    const initial = btn.getAttribute('aria-pressed')
    fireEvent.click(btn)
    expect(btn.getAttribute('aria-pressed')).toBe(initial === 'true' ? 'false' : 'true')
  })
})

describe('ControlRail — error', () => {
  it('renders the error message when present', () => {
    renderRail({ error: 'boom' })
    expect(screen.getByText('boom')).toBeInTheDocument()
  })

  it('renders nothing when error is null', () => {
    const { container } = renderRail({ error: null })
    expect(container.querySelector('.railError')).not.toBeInTheDocument()
  })
})
