import type { MouseEvent } from 'react'
import { useFeltState } from './FeltStateContext'

/**
 * zone() ported to a hook — hover sets the #readout text; click
 * spends the selected denom from the rack onto this zone's chip
 * stack; right-click pops one back. Chip placement is a DEV TOOL for
 * validating bet-position coordinates, not the real interaction model
 * — the live felt will place chips from BetPlaced/BetResolved events,
 * never clicks (Step 3).
 *
 * Omit chipId/cx/cy for a hover-only zone (e.g. an outer frame that
 * just shows info text but isn't itself a bet position).
 */
export function useZone(info: string, chipId?: string, cx?: number, cy?: number) {
  const { setHoverInfo, placeChip, removeChip, selectedDenom } = useFeltState()

  const onMouseEnter = () => setHoverInfo(info)
  const onMouseLeave = () => setHoverInfo('hover a zone…')

  if (!chipId) {
    return { onMouseEnter, onMouseLeave }
  }

  return {
    onMouseEnter,
    onMouseLeave,
    onClick: () => placeChip(chipId, cx ?? 0, cy ?? 0, selectedDenom),
    onContextMenu: (e: MouseEvent) => {
      e.preventDefault()
      removeChip(chipId)
    },
    style: { cursor: 'pointer' as const },
  }
}
