/**
 * The real thing (Step 3 + 3b): create/start a live bot table via the
 * roster panel's lineup builder, and watch it play out on the
 * faithful felt — dice, chips, toasts, shooter history, pace controls,
 * and a live roster/play-by-play, all on one page. The old Observatory
 * harness (a bare button strip + raw-JSON dump) is gone entirely.
 */
import { useCallback, useRef, useState } from 'react'

import { LiveFelt } from './components/felt/Felt'
import { initialRollLogState, rollLogReducer, type RollLogState } from './components/felt/state/liveRollLog'
import { initialPlayByPlay, playByPlayReducer } from './components/felt/state/playByPlay'
import { netFor } from './components/felt/state/useFeltLiveState'
import type { RosterEntry } from './components/felt/types'
import { RosterPanel, type RosterRow } from './components/roster/RosterPanel'
import { api, type PlayerSpec, type TableSnapshot } from './lib/api'
import { connectTableStream, type StreamHandle } from './lib/sse'
import { initialState, tableReducer, type TableState } from './lib/tableReducer'

const DEFAULT_ROLL_DELAY_MS = 500

export default function App() {
  const [snapshot, setSnapshot] = useState<TableSnapshot | null>(null)
  const [state, setState] = useState<TableState>(initialState)
  const [rollLog, setRollLog] = useState<RollLogState>(initialRollLogState)
  const [playByPlay, setPlayByPlay] = useState<string[]>(initialPlayByPlay)
  const [playerName, setPlayerName] = useState<string>('')
  const [turboOn, setTurboOn] = useState(false)
  const [creating, setCreating] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const stream = useRef<StreamHandle | null>(null)

  const attach = useCallback((tableId: string) => {
    stream.current?.close()
    setState(initialState())
    setRollLog(initialRollLogState())
    setPlayByPlay(initialPlayByPlay())
    stream.current = connectTableStream(tableId, (envelope) => {
      setState((s) => tableReducer(s, envelope))
      setRollLog((l) => rollLogReducer(l, envelope))
      setPlayByPlay((lines) => playByPlayReducer(lines, envelope))
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

  const roster: RosterEntry[] = snapshot?.players.map((p) => ({ name: p.name, strategy: p.strategy })) ?? []
  const rosterRows: RosterRow[] =
    snapshot?.players.map((p) => {
      const live = state.players.get(p.name)
      return { name: p.name, strategy: p.strategy, bankroll: live?.bankroll ?? p.bankroll ?? 0, net: netFor(live) }
    }) ?? []

  return (
    <LiveFelt
      tableState={state}
      rollLog={rollLog}
      playerName={playerName}
      setPlayerName={setPlayerName}
      roster={roster}
      setTableState={setState}
      sessionState={snapshot?.state ?? null}
      onPauseResume={handlePauseResume}
      onTurbo={handleTurbo}
      turboOn={turboOn}
      onStep={handleStep}
      rosterPanel={
        <RosterPanel
          hasTable={snapshot !== null}
          creating={creating}
          error={error}
          onCreateAndStart={handleCreateAndStart}
          rosterRows={rosterRows}
          selectedPlayer={playerName}
          onSelectPlayer={setPlayerName}
          playByPlay={playByPlay}
        />
      }
    />
  )
}
