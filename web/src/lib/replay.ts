/**
 * Replay driver (D2 / Step 4 core): a recorded session pages through
 * the SAME reducer the live felt uses — replay and live are one
 * renderer fed from different sources.
 *
 * The controller is deliberately clock-free: it exposes step / stepRoll
 * / seek and the UI owns playback time (a timer calling stepRoll at the
 * chosen speed, a scrubber calling seek). No server-side replay clock,
 * no timers to mock in tests.
 */
import type { Envelope } from './events'
import { initialState, tableReducer, type TableState } from './tableReducer'

export class ReplayController {
  private readonly events: Envelope[]
  private cursor = 0 // index of the next event to apply
  state: TableState = initialState()

  constructor(events: Envelope[]) {
    this.events = events
  }

  /** seq of the last applied event; -1 before the first. */
  get position(): number {
    return this.cursor - 1
  }

  get length(): number {
    return this.events.length
  }

  get atEnd(): boolean {
    return this.cursor >= this.events.length
  }

  /** Apply one event. Returns false at end of stream. */
  step(): boolean {
    if (this.atEnd) return false
    this.state = tableReducer(this.state, this.events[this.cursor])
    this.cursor += 1
    return true
  }

  /** Advance through the next DiceRolled (inclusive) — one "beat" of
   * table time, the natural unit for speed control. */
  stepRoll(): boolean {
    if (this.atEnd) return false
    while (this.step()) {
      if (this.events[this.cursor - 1].type === 'DiceRolled') break
    }
    return true
  }

  /** Jump to a seq (inclusive). The reducer is pure, so seeking is a
   * rebuild — cheap enough for scrubbing; throttle in the UI if not. */
  seek(seq: number): void {
    if (seq < this.position) {
      this.state = initialState()
      this.cursor = 0
    }
    while (this.position < seq && this.step()) {
      /* advance */
    }
  }
}
