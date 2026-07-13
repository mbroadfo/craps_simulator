/**
 * The real thing (Step 3 + 3b + 3c): build a lineup and Start a live
 * bot table in ControlStripe (the horizontal band between the felt
 * and the session graph), watch it play out on the faithful felt —
 * dice, chips, toasts, shooter history — with Play/Roll/Turbo/Reset
 * always reachable in the stripe below, a lean PlayerSidebar next to
 * the felt for switching perspective (name/strategy/bankroll per
 * row), and a full-height session graph to scroll down to. The old
 * Observatory harness (a bare button strip + raw-JSON dump) is gone
 * entirely, and so is the right-side roster/play-by-play panel that
 * briefly replaced it.
 */
import { useCallback, useRef, useState } from 'react'

import { ControlStripe } from './components/controlstripe/ControlStripe'
import { LiveFelt } from './components/felt/Felt'
import { initialRollLogState, rollLogReducer, type RollLogState } from './components/felt/state/liveRollLog'
import { netFor } from './components/felt/state/useFeltLiveState'
import type { RosterEntry } from './components/felt/types'
import { PlayerSidebar, type PlayerSidebarRow } from './components/playersidebar/PlayerSidebar'
import { SessionGraph, type GraphPlayer } from './components/sessiongraph/SessionGraph'
import { api, type PlayerSpec, type TableSnapshot } from './lib/api'
import { connectTableStream, type StreamHandle } from './lib/sse'
import { initialState, tableReducer, type TableState } from './lib/tableReducer'

const DEFAULT_ROLL_DELAY_MS = 500

// Qualitative palette for per-player graph lines — distinct hues, not
// tied to any win/loss meaning (unlike the felt's own red/green).
const PLAYER_COLORS = ['#4a7fd4', '#e8a04a', '#2ecc71', '#d95f4c', '#9b6fd1', '#4fd1c5', '#e0c341', '#c9a84c']

export default function App() {
  const [snapshot, setSnapshot] = useState<TableSnapshot | null>(null)
  const [state, setState] = useState<TableState>(initialState)
  const [rollLog, setRollLog] = useState<RollLogState>(initialRollLogState)
  const [playerName, setPlayerName] = useState<string>('')
  const [turboOn, setTurboOn] = useState(false)
  const [creating, setCreating] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const stream = useRef<StreamHandle | null>(null)

  const attach = useCallback((tableId: string) => {
    stream.current?.close()
    setState(initialState())
    setRollLog(initialRollLogState())
    stream.current = connectTableStream(tableId, (envelope) => {
      setState((s) => tableReducer(s, envelope))
      setRollLog((l) => rollLogReducer(l, envelope))
    })
  }, [])

  const handleCreateAndStart = useCallback(
    async (lineup: PlayerSpec[]) => {
      try {
        setCreating(true)
        setError(null)
        const created = await api.createTable({
          players: lineup,
          num_shooters: 10,
          roll_delay_ms: DEFAULT_ROLL_DELAY_MS,
        })
        attach(created.table_id)
        setPlayerName(created.players[0]?.name ?? '')
        setTurboOn(false)
        setSnapshot(await api.start(created.table_id))
      } catch (e) {
        setError(String(e))
      } finally {
        setCreating(false)
      }
    },
    [attach],
  )

  const handlePauseResume = useCallback(async () => {
    if (!snapshot) return
    setSnapshot(snapshot.state === 'paused' ? await api.resume(snapshot.table_id) : await api.pause(snapshot.table_id))
  }, [snapshot])

  const handleTurbo = useCallback(async () => {
    if (!snapshot) return
    const next = !turboOn
    setSnapshot(await api.setPace(snapshot.table_id, next ? 0 : DEFAULT_ROLL_DELAY_MS))
    setTurboOn(next)
  }, [snapshot, turboOn])

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
    setPlayerName('')
    setTurboOn(false)
    setError(null)
  }, [snapshot])

  const roster: RosterEntry[] = snapshot?.players.map((p) => ({ name: p.name, strategy: p.strategy })) ?? []
  const rosterRows: PlayerSidebarRow[] =
    snapshot?.players.map((p) => {
      const live = state.players.get(p.name)
      return { name: p.name, strategy: p.strategy, bankroll: live?.bankroll ?? p.bankroll ?? 0, net: netFor(live) }
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

  return (
    <>
      <LiveFelt
        tableState={state}
        rollLog={rollLog}
        playerName={playerName}
        setPlayerName={setPlayerName}
        roster={roster}
        setTableState={setState}
        sidebar={<PlayerSidebar roster={rosterRows} selectedPlayer={playerName} onSelectPlayer={setPlayerName} />}
      />
      <ControlStripe
        hasTable={snapshot !== null}
        creating={creating}
        error={error}
        onCreateAndStart={handleCreateAndStart}
        onReset={handleReset}
        sessionState={snapshot?.state ?? null}
        onPauseResume={handlePauseResume}
        onTurbo={handleTurbo}
        turboOn={turboOn}
        onStep={handleStep}
      />
      <SessionGraph players={graphPlayers} totalRolls={rollLog.rolls.length} sevenOutIndices={sevenOutIndices} />
    </>
  )
}
