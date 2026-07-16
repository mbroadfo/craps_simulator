/**
 * The session's bankroll-over-time graph — one line per player, a
 * dashed baseline at each player's starting bankroll, a shaded band
 * showing how much of each player's bankroll is currently riding on
 * active bets, and a labeled marker at every shooter change. Revives
 * what the old CLI Visualizer (craps/visualizer.py) plotted with
 * matplotlib, as a live interactive chart instead of a static PNG —
 * built on recharts (added for this) rather than hand-rolled SVG, to
 * get hover tooltips and point markers without reimplementing a
 * charting library's worth of interaction logic by hand.
 *
 * Deliberately rendered below the felt, not inside it — this is
 * session-wide history across every seated player, not a single
 * seat's view, so it lives in App.tsx's domain alongside RosterPanel
 * rather than threaded through FeltUiState.
 *
 * Styled as a light theme on purpose (Mike's explicit call, matching
 * a reference chart image) even though it sits below the felt's dark
 * casino theme — see SessionGraph.css's own note.
 */
import { useState } from 'react'
import {
  Area,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  type TooltipContentProps,
} from 'recharts'
import './SessionGraph.css'
import { bandKey, betKey, buildChartRows, deltaKey, shooterBoundaryRolls, type GraphPlayer } from './graphMath'

export type { GraphPlayer }

function ChartTooltip({ active, payload, label }: TooltipContentProps) {
  if (!active || !payload || payload.length === 0) return null
  const rows = payload.filter((entry) => typeof entry.dataKey === 'string' && !(entry.dataKey as string).includes('__'))
  if (rows.length === 0) return null

  return (
    <div className="sessionGraphTooltip">
      <div className="sessionGraphTooltipRoll">Roll {label}</div>
      {rows.map((entry) => {
        // dataKey is the player's own name (the actual data field);
        // `name` is whatever display label the Line was given
        // (strategy name) — the row's derived bet/delta keys are
        // always built from the player name, not the display label.
        const playerKey = entry.dataKey as string
        const row = entry.payload as Record<string, number>
        const bankroll = typeof entry.value === 'number' ? entry.value : Number(entry.value)
        const bet = row[betKey(playerKey)]
        const delta = row[deltaKey(playerKey)]
        return (
          <div key={playerKey} className="sessionGraphTooltipRow">
            <span className="sessionGraphTooltipName" style={{ color: entry.color }}>{entry.name}</span>
            {typeof delta === 'number' && delta !== 0 && (
              <span className={'sessionGraphTooltipDelta ' + (delta >= 0 ? 'pos' : 'neg')}>
                {delta >= 0 ? '+' : ''}
                {Math.round(delta)}
              </span>
            )}
            <span>Bankroll ${Math.round(bankroll).toLocaleString()}</span>
            {typeof bet === 'number' && <span>At risk ${Math.round(bet).toLocaleString()}</span>}
          </div>
        )
      })}
    </div>
  )
}

export function SessionGraph({
  players,
  totalRolls,
  sevenOutIndices,
}: {
  players: GraphPlayer[]
  totalRolls: number
  sevenOutIndices: number[]
}) {
  const [hidden, setHidden] = useState<Set<string>>(new Set())
  const withData = players.filter((p) => p.history.length > 0)
  const rows = buildChartRows(withData, totalRolls)
  const boundaries = shooterBoundaryRolls(sevenOutIndices)

  const toggle = (name: string) => {
    setHidden((prev) => {
      const next = new Set(prev)
      if (next.has(name)) next.delete(name)
      else next.add(name)
      return next
    })
  }

  // All seats start from the same house-rules bankroll — one shared
  // reference line reads far cleaner than one per player (which,
  // dashed and overlapping at the same value, looked like stray
  // duplicate lines rather than N baselines that happen to coincide).
  const startingBankroll = withData[0]?.history[0]

  return (
    <div className="sessionGraph">
      {withData.length === 0 ? (
        <div className="sessionGraphEmpty">No rolls yet — start a table to watch bankrolls play out here.</div>
      ) : (
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={rows} margin={{ top: 8, right: 24, bottom: 8, left: 8 }}>
            <CartesianGrid stroke="#e0e0e0" />
            <XAxis dataKey="roll" tick={{ fontSize: 11 }} />
            <YAxis tick={{ fontSize: 11 }} label={{ value: 'Value', angle: -90, position: 'insideLeft' }} />
            <Tooltip content={ChartTooltip} />
            <Legend
              verticalAlign="top"
              onClick={(entry) => toggle(String(entry.dataKey))}
              formatter={(value) => (
                <span style={hidden.has(String(value)) ? { textDecoration: 'line-through', opacity: 0.5 } : undefined}>{value}</span>
              )}
            />

            {boundaries.map((b) => (
              <ReferenceLine
                key={b.roll}
                x={b.roll}
                stroke="#e8908a"
                strokeWidth={1.5}
                label={{ value: `Shooter ${b.shooterNum}`, position: 'insideBottomLeft', fill: '#8a6a66', fontSize: 11 }}
              />
            ))}

            {startingBankroll !== undefined && (
              <ReferenceLine y={startingBankroll} stroke="#333333" strokeDasharray="4 4" strokeOpacity={0.6} />
            )}

            {withData.map((p) => (
              <Area
                key={`${p.name}-band`}
                dataKey={(row: Record<string, unknown>) => row[bandKey(p.name)]}
                stroke="none"
                fill={p.color}
                fillOpacity={0.14}
                hide={hidden.has(p.name)}
                isAnimationActive={false}
                legendType="none"
              />
            ))}

            {withData.map((p) => (
              <Line
                key={p.name}
                dataKey={p.name}
                name={p.strategy}
                stroke={p.color}
                strokeWidth={2}
                dot={{ r: 2.5, fill: p.color, strokeWidth: 0 }}
                activeDot={{ r: 5 }}
                hide={hidden.has(p.name)}
                connectNulls={false}
                isAnimationActive={false}
              />
            ))}
          </ComposedChart>
        </ResponsiveContainer>
      )}
    </div>
  )
}
