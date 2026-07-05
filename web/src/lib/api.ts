/** REST client for the observatory server (Step 1 endpoints). */

export interface PlayerSpec {
  name: string
  strategy: string
}

export interface CreateTableRequest {
  table_id?: string
  players: PlayerSpec[]
  house_rules?: Record<string, unknown>
  num_shooters?: number
  max_rolls?: number
  roll_delay_ms?: number
  dice_seed?: number
  record?: boolean
}

export interface Seat {
  name: string
  strategy: string
  bankroll: number | null
}

export interface TableSnapshot {
  table_id: string
  state: 'created' | 'running' | 'paused' | 'finished' | 'stopped'
  roll_delay_ms: number
  next_seq: number
  session_rolls: number
  shooter_index: number
  puck_on: boolean
  point: number | null
  players: Seat[]
  recording: string | null
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, init)
  if (!response.ok) {
    const detail = await response.text()
    throw new Error(`${init?.method ?? 'GET'} ${path} → ${response.status}: ${detail}`)
  }
  return response.json() as Promise<T>
}

const post = <T,>(path: string, body?: unknown): Promise<T> =>
  request<T>(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: body === undefined ? undefined : JSON.stringify(body),
  })

export const api = {
  listStrategies: () => request<string[]>('/tables/strategies'),
  listTables: () => request<TableSnapshot[]>('/tables'),
  getTable: (id: string) => request<TableSnapshot>(`/tables/${id}`),
  getStats: (id: string) => request<Record<string, unknown>>(`/tables/${id}/stats`),
  createTable: (body: CreateTableRequest) => post<TableSnapshot>('/tables', body),
  start: (id: string) => post<TableSnapshot>(`/tables/${id}/start`),
  pause: (id: string) => post<TableSnapshot>(`/tables/${id}/pause`),
  resume: (id: string) => post<TableSnapshot>(`/tables/${id}/resume`),
  stop: (id: string) => post<TableSnapshot>(`/tables/${id}/stop`),
  setPace: (id: string, rollDelayMs: number) =>
    post<TableSnapshot>(`/tables/${id}/pace`, { roll_delay_ms: rollDelayMs }),
}
