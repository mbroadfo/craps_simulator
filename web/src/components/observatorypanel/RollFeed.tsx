import type { PlayByPlayEntry } from '../felt/state/playByPlay'
import './ObservatoryPanel.css'

/** Scrolling event log, newest at top — a styled revival of playByPlay,
 * back on request now that it lives in its own section instead of
 * jammed into the old roster panel. */
export function RollFeed({ entries }: { entries: PlayByPlayEntry[] }) {
  return (
    <div className="obsSection">
      <div className="obsHeader">Roll Feed</div>
      {entries.length === 0 ? (
        <div className="obsEmpty">No rolls yet</div>
      ) : (
        <div className="obsFeedList">
          {entries.map((e) => (
            <div key={e.id} className={'obsFeedRow ' + e.kind}>
              {e.text}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
