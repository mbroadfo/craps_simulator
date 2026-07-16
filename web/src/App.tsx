/**
 * The real thing (Step 3 + 3b + 3c + Observatory panel): build a
 * lineup in the Observatory panel's checkbox list, then Start the
 * table from ControlRail — a fixed, always-visible action bar (see
 * ObservatoryPanel.tsx) whose Start button doubles as the Play/Pause
 * toggle. Starting does not set the game rolling by itself: it lands
 * paused, and from there the game only ever progresses via Play,
 * Roll (single step), or Turbo, all in that same rail. Watch it play
 * out on the faithful felt — dice, chips, toasts, shooter history —
 * alongside a bot roster with sparklines for switching perspective, a
 * leaderboard, a roll-distribution chart, a roll feed, and a full-
 * height session graph to scroll down to. The old ControlStripe/
 * PlayerSidebar pair is gone, folded into the Observatory panel.
 */
import { useCallback, useEffect, useRef, useState } from 'react'

import { LiveFelt } from './components/felt/Felt'
import { initialRollLogState, rollLogReducer, type RollLogState } from './components/felt/state/liveRollLog'
import { initialPlayByPlay, playByPlayReducer, type PlayByPlayEntry } from './components/felt/state/playByPlay'
import { netFor } from './components/felt/state/useFeltLiveState'
import type { RosterEntry } from './components/felt/types'
import type { ObsPlayerRow } from './components/observatorypanel/BotRoster'
import { MAX_SPEED } from './components/observatorypanel/ControlRail'
import { ObservatoryPanel, type Seat } from './components/observatorypanel/ObservatoryPanel'
import { SessionGraph, type GraphPlayer } from './components/sessiongraph/SessionGraph'
import { api, type TableSnapshot } from './lib/api'
import { connectTableStream, type StreamHandle } from './lib/sse'
import { initialState, tableReducer, type TableState } from './lib/tableReducer'

const DEFAULT_ROLL_DELAY_MS = 500
const DEFAULT_NUM_SHOOTERS = 10

// Seats are keyed by strategy name, one-to-one — the player *name*
// sent to the backend is just the strategy name too (PlayerSpec still
// carries name/strategy as separate fields, so this is free to change
// later without a data-model migration).
const DEFAULT_CHECKED = new Set(['Pass-Line', 'Iron Cross', '3-Point Molly'])

// Qualitative palette for per-player graph lines — distinct hues, not
// tied to any win/loss meaning (unlike the felt's own red/green).
const PLAYER_COLORS = ['#4a7fd4', '#e8a04a', '#2ecc71', '#d95f4c', '#9b6fd1', '#4fd1c5', '#e0c341', '#c9a84c']

export default function App() {
  const [snapshot, setSnapshot] = useState<TableSnapshot | null>(null)
  const [state, setState] = useState<TableState>(initialState)
  const [rollLog, setRollLog] = useState<RollLogState>(initialRollLogState)
  const [feed, setFeed] = useState<PlayByPlayEntry[]>(initialPlayByPlay)
  const [playerName, setPlayerName] = useState<string>('')
  const [speed, setSpeed] = useState(1)
  const [numShooters, setNumShooters] = useState(DEFAULT_NUM_SHOOTERS)
  const [seats, setSeats] = useState<Seat[]>([])
  const [creating, setCreating] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const stream = useRef<StreamHandle | null>(null)

  // Lifted out of ObservatoryPanel (rather than local state there) so
  // ControlRail's Start button can read the current lineup selection
  // too — see ObservatoryPanel.tsx's header comment.
  useEffect(() => {
    api.listStrategies().then((list) => {
      setSeats(list.map((name) => ({ name, enabled: DEFAULT_CHECKED.has(name) })))
    })
  }, [])

  const handleToggleSeat = useCallback((index: number) => {
    setSeats((prev) => prev.map((s, i) => (i === index ? { ...s, enabled: !s.enabled } : s)))
  }, [])
  const handleSelectAll = useCallback(() => setSeats((prev) => prev.map((s) => ({ ...s, enabled: true }))), [])
  const handleClearAll = useCallback(() => setSeats((prev) => prev.map((s) => ({ ...s, enabled: false }))), [])

  const attach = useCallback((tableId: string) => {
    stream.current?.close()
    setState(initialState())
    setRollLog(initialRollLogState())
    setFeed(initialPlayByPlay())
    stream.current = connectTableStream(tableId, (envelope) => {
      setState((s) => tableReducer(s, envelope))
      setRollLog((l) => rollLogReducer(l, envelope))
      setFeed((f) => playByPlayReducer(f, envelope))
    })
  }, [])

  // Creates the table and immediately pauses it — Start does not set
  // the game rolling, it just makes the rail's Play/Roll/Turbo
  // controls available. start() has to run first: pause() only
  // accepts a table already in the "running" state.
  const handleStart = useCallback(async () => {
    try {
      setCreating(true)
      setError(null)
      const lineup = seats.filter((s) => s.enabled).map((s) => ({ name: s.name, strategy: s.name }))
      const created = await api.createTable({
        players: lineup,
        num_shooters: numShooters,
        roll_delay_ms: DEFAULT_ROLL_DELAY_MS,
      })
      attach(created.table_id)
      setPlayerName(created.players[0]?.name ?? '')
      setSpeed(1)
      await api.start(created.table_id)
      setSnapshot(await api.pause(created.table_id))
    } catch (e) {
      setError(String(e))
    } finally {
      setCreating(false)
    }
  }, [attach, numShooters, seats])

  const handlePauseResume = useCallback(async () => {
    if (!snapshot) return
    setSnapshot(snapshot.state === 'paused' ? await api.resume(snapshot.table_id) : await api.pause(snapshot.table_id))
  }, [snapshot])

  const handleSpeedChange = useCallback(
    async (next: number) => {
      setSpeed(next)
      if (!snapshot) return
      const rollDelayMs = next >= MAX_SPEED ? 0 : Math.round(DEFAULT_ROLL_DELAY_MS / next)
      setSnapshot(await api.setPace(snapshot.table_id, rollDelayMs))
    },
    [snapshot],
  )

  const handleStep = useCallback(async () => {
    if (!snapshot) return
    setSnapshot(await api.step(snapshot.table_id))
  }, [snapshot])

  // Tears down the current table (best-effort — it may already be
  // finished server-side) and drops the UI back to the lineup builder
  // for a fresh Start, without a page reload.
  const handleReset = useCallback(async () => {
    if (snapshot && snapshot.state !== 'finished' && snapshot.state !== 'stopped') {
      await api.stop(snapshot.table_id).catch(() => {})
    }
    stream.current?.close()
    setSnapshot(null)
    setState(initialState())
    setRollLog(initialRollLogState())
    setFeed(initialPlayByPlay())
    setPlayerName('')
    setSpeed(1)
    setError(null)
  }, [snapshot])

  const roster: RosterEntry[] = snapshot?.players.map((p) => ({ name: p.name, strategy: p.strategy })) ?? []
  const obsRoster: ObsPlayerRow[] =
    snapshot?.players.map((p, i) => {
      const live = state.players.get(p.name)
      return {
        name: p.name,
        strategy: p.strategy,
        color: PLAYER_COLORS[i % PLAYER_COLORS.length],
        bankroll: live?.bankroll ?? p.bankroll ?? 0,
        net: netFor(live),
        startingBankroll: live && live.history.length > 0 ? live.history[0] : null,
        history: live?.history ?? [],
      }
    }) ?? []
  const graphPlayers: GraphPlayer[] =
    snapshot?.players.map((p, i) => ({
      name: p.name,
      strategy: p.strategy,
      color: PLAYER_COLORS[i % PLAYER_COLORS.length],
      history: state.players.get(p.name)?.history ?? [],
      atRiskHistory: state.players.get(p.name)?.atRiskHistory ?? [],
    })) ?? []
  const sevenOutIndices = rollLog.rolls.reduce<number[]>((acc, r, i) => {
    if (r.type === 'seven-out') acc.push(i)
    return acc
  }, [])
  const rollTotals = rollLog.rolls.map((r) => r.total)

  return (
    <>
      <LiveFelt
        tableState={state}
        rollLog={rollLog}
        playerName={playerName}
        setPlayerName={setPlayerName}
        roster={roster}
        setTableState={setState}
        sidebar={
          <ObservatoryPanel
            hasTable={snapshot !== null}
            seats={seats}
            onToggleSeat={handleToggleSeat}
            onSelectAll={handleSelectAll}
            onClearAll={handleClearAll}
            numShooters={numShooters}
            onNumShootersChange={setNumShooters}
            canStart={seats.some((s) => s.enabled)}
            creating={creating}
            error={error}
            onStart={handleStart}
            sessionState={snapshot?.state ?? null}
            onPauseResume={handlePauseResume}
            onStep={handleStep}
            onReset={handleReset}
            speed={speed}
            onSpeedChange={handleSpeedChange}
            roster={obsRoster}
            selectedPlayer={playerName}
            onSelectPlayer={setPlayerName}
            feed={feed}
            rolls={rollTotals}
            dice={state.dice}
          />
        }
      />
      <SessionGraph players={graphPlayers} totalRolls={rollLog.rolls.length} sevenOutIndices={sevenOutIndices} />
    </>
  )
}
