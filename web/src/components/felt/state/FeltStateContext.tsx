import { createContext, useContext, type ReactNode } from 'react'
import type { FeltUiState } from '../types'
import { useFeltDevState } from './useFeltDevState'

const FeltStateContext = createContext<FeltUiState | null>(null)

/**
 * `value` lets a caller supply a pre-built FeltUiState (Step 3's
 * useFeltLiveState, in spectator mode) instead of the dev-tool state.
 * useFeltDevState() is always called (rules-of-hooks) — its result is
 * just ignored when a live value is supplied.
 */
export function FeltStateProvider({ children, value }: { children: ReactNode; value?: FeltUiState }) {
  const devState = useFeltDevState()
  const state = value ?? devState
  return <FeltStateContext.Provider value={state}>{children}</FeltStateContext.Provider>
}

export function useFeltState(): FeltUiState {
  const ctx = useContext(FeltStateContext)
  if (!ctx) throw new Error('useFeltState must be used within a FeltStateProvider')
  return ctx
}
