import { createContext, useContext, type ReactNode } from 'react'
import { useFeltDevState, type FeltDevState } from './useFeltDevState'

const FeltStateContext = createContext<FeltDevState | null>(null)

export function FeltStateProvider({ children }: { children: ReactNode }) {
  const state = useFeltDevState()
  return <FeltStateContext.Provider value={state}>{children}</FeltStateContext.Provider>
}

export function useFeltState(): FeltDevState {
  const ctx = useContext(FeltStateContext)
  if (!ctx) throw new Error('useFeltState must be used within a FeltStateProvider')
  return ctx
}
