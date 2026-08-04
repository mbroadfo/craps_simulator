/**
 * A roster-row speech bubble showing a bot's static come-out dealer
 * call (Observatory panel, Tier 1 — no dynamic mid-hand narration
 * yet). Purely presentational: mounted = visible, unmounted = gone.
 * App.tsx owns the 3-second lifecycle (a single setTimeout that
 * clears the active shooter, same pattern the win/loss fade-up toasts
 * use in useFeltLiveState.ts/useFeltDevState.ts) — this component has
 * no timer of its own. The entrance/hold/exit animation is one
 * `dealerCallBubble` keyframe in ObservatoryPanel.css spanning the
 * component's full mounted lifetime, not a `visible`-prop toggle.
 */
export function DealerCallBubble({ text }: { text: string }) {
  return <div className="dealerCallBubble">{text}</div>
}
