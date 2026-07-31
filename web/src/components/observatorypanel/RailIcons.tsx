/**
 * Roll and Turbo used to be the emoji glyphs 🎲/⏩ — Windows renders
 * emoji-presentation characters in its own full-color emoji font,
 * ignoring the button's `color`, while the rail's other buttons
 * (▶/⏸/✕, plain text glyphs) correctly pick up currentColor. That
 * mismatch made the row look like an accident, not four buttons in
 * one control cluster. These two are small inline SVGs instead, so
 * every icon in the rail is colored (and dimmed when disabled) the
 * same way.
 */
export function DiceIcon() {
  return (
    <svg viewBox="0 0 20 20" width={16} height={16} aria-hidden="true">
      <rect x={1.5} y={1.5} width={17} height={17} rx={3} fill="none" stroke="currentColor" strokeWidth={1.5} />
      <circle cx={6} cy={6} r={1.6} fill="currentColor" />
      <circle cx={14} cy={6} r={1.6} fill="currentColor" />
      <circle cx={10} cy={10} r={1.6} fill="currentColor" />
      <circle cx={6} cy={14} r={1.6} fill="currentColor" />
      <circle cx={14} cy={14} r={1.6} fill="currentColor" />
    </svg>
  )
}

export function TurboIcon() {
  return (
    <svg viewBox="0 0 20 20" width={16} height={16} aria-hidden="true" fill="currentColor">
      <path d="M2 3l7 7-7 7V3z" />
      <path d="M10 3l7 7-7 7V3z" />
    </svg>
  )
}

/** A repeat/loop glyph for the Autoplay toggle — deliberately not another triangle or chevron (Roll and Turbo already use those), so "roll continuously" reads as a distinct action from "roll once" or "jump to max speed" at a glance. */
export function AutoplayIcon() {
  return (
    <svg viewBox="0 0 20 20" width={16} height={16} aria-hidden="true">
      <path
        d="M4 8a6 6 0 0 1 10.5-4M16 12a6 6 0 0 1-10.5 4"
        fill="none"
        stroke="currentColor"
        strokeWidth={1.6}
        strokeLinecap="round"
      />
      <path d="M14.5 2.5v4h-4" fill="none" stroke="currentColor" strokeWidth={1.6} strokeLinecap="round" strokeLinejoin="round" />
      <path d="M5.5 17.5v-4h4" fill="none" stroke="currentColor" strokeWidth={1.6} strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}
