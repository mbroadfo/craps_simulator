import { useFeltState } from '../state/FeltStateContext'

export function fmtMoney(n: number): string {
  return `$${Math.round(n).toLocaleString()}`
}
export function fmtSigned(n: number): string {
  const s = Math.round(n)
  return (s > 0 ? '+' : '') + s.toLocaleString()
}

/**
 * gatherLocalStats() in the prototype — window.updateSidebar(stats) is
 * the public contract a real backend would call directly (Step 3).
 * This prototype has no bet-resolution or strategy tracking, so this
 * only fills the fields it genuinely has (table config placeholders,
 * roll distribution, rolls/hands, rack/bankroll, bets-on-table).
 * Strategy P&L, Efficiency, Hits/Rate, Shooter net, and Net P&L stay
 * undefined — rendered as "—" by StatsSection — until something real
 * provides them.
 */
export function useLocalStats() {
  const { rack, chips, rollHistory } = useFeltState()

  const rackTotal = Object.entries(rack).reduce((sum, [denom, count]) => sum + Number(denom) * count, 0)
  const feltTotal = Object.values(chips).reduce((sum, zone) => sum + zone.denoms.reduce((a, b) => a + b, 0), 0)

  const distribution: Record<number, number> = {}
  for (let n = 2; n <= 12; n++) distribution[n] = 0
  for (const r of rollHistory) distribution[r.total]++

  return {
    // Static display values — no HouseRules/config source in this prototype
    min: 10,
    max: 1000,
    odds: '3-4-5x',
    oddsMax: 2000,
    rolls: rollHistory.length,
    hands: rollHistory.filter((r) => r.type === 'seven-out').length,
    distribution,
    rack: rackTotal,
    bankroll: rackTotal + feltTotal,
    betsOn: Object.keys(chips).length,
  }
}
