/**
 * Dev harness (deliberately unstyled): proves the non-visual pipeline
 * end-to-end - create/start a table, stream it over SSE, reduce to
 * TableState, and inspect the raw state. The faithful table (Step 2
 * visuals) replaces this entirely; nothing here is load-bearing.
 */
import { useCallback, useRef, useState } from 'react'

import { api, type TableSnapshot } from './lib/api'
import { connectTableStream, type StreamHandle } from './lib/sse'
import { initialState, tableReducer, type TableState } from './lib/tableReducer'

const DEMO_LINEUP = [
  { name: 'Molly', strategy: '3-Point Molly' },
  { name: 'Crosstopher', strategy: 'Iron Cross' },
  { name: 'Linus', strategy: 'Pass-Line' },
]

export default function App() {
  const [snapshot, setSnapshot] = useState<TableSnapshot | null>(null)
  const [state, setState] = useState<TableState>(initialState)
  const [error, setError] = useState<string | null>(null)
  const stream = useRef<StreamHandle | null>(null)

  const attach = useCallback((tableId: string) => {
    stream.current?.close()
    setState(initialState())
    stream.current = connectTableStream(tableId, (envelope) => {
      setState((s) => tableReducer(s, envelope))
    })
  }, [])

  const createAndStart = useCallback(async () => {
    try {
      setError(null)
      const created = await api.createTable({
        players: DEMO_LINEUP,
        num_shooters: 10,
        roll_delay_ms: 500,
      })
      attach(created.table_id)
      setSnapshot(await api.start(created.table_id))
    } catch (e) {
      setError(String(e))
    }
  }, [attach])

  const control = (action: (id: string) => Promise<TableSnapshot>) => async () => {
    if (snapshot) setSnapshot(await action(snapshot.table_id))
  }

  return (
    <main className="p-4 font-mono text-sm">
      <h1 className="text-lg font-bold">Observatory pipeline harness</h1>
      <div className="my-2 flex gap-2">
        <button className="border px-2 py-1" onClick={createAndStart}>
          create + start
        </button>
        <button className="border px-2 py-1" onClick={control(api.pause)}>
          pause
        </button>
        <button className="border px-2 py-1" onClick={control(api.resume)}>
          resume
        </button>
        <button className="border px-2 py-1" onClick={control((id) => api.setPace(id, 0))}>
          turbo
        </button>
      </div>
      {error && <pre className="text-red-600">{error}</pre>}
      <pre>
        {JSON.stringify(
          {
            table: state.tableId,
            roll: state.rollNumber,
            dice: state.dice,
            phase: state.phase,
            point: state.point,
            shooter: state.shooterName,
            finished: state.finished,
            orphans: state.orphans.length,
            players: Object.fromEntries(
              [...state.players].map(([n, p]) => [n, { bankroll: p.bankroll, atRisk: p.atRisk }]),
            ),
            chips: [...state.chips.values()].map(
              (c) => `${c.player} ${c.betType} ${JSON.stringify(c.number)} $${c.amounts.join('+')} (${c.status})`,
            ),
          },
          null,
          2,
        )}
      </pre>
    </main>
  )
}
