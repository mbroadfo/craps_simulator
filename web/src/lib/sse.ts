/**
 * SSE client for the live table stream (D1). The browser's EventSource
 * reconnects automatically and sends Last-Event-ID, which the server
 * answers with a gapless resume — no client-side gap logic needed.
 * A fresh connection replays the session from seq 0, so a late-joining
 * felt builds complete state.
 */
import { EVENT_TYPES, type Envelope } from './events'

export interface StreamHandle {
  close: () => void
}

export function connectTableStream(
  tableId: string,
  onEnvelope: (e: Envelope) => void,
  onError?: (e: Event) => void,
): StreamHandle {
  const source = new EventSource(`/tables/${encodeURIComponent(tableId)}/stream`)
  for (const type of EVENT_TYPES) {
    source.addEventListener(type, (event) => {
      onEnvelope(JSON.parse((event as MessageEvent<string>).data) as Envelope)
    })
  }
  if (onError) source.onerror = onError
  return { close: () => source.close() }
}
