import { useSidebarAutoFit } from '../state/useSidebarAutoFit'
import { DistributionSection } from './DistributionSection'
import { StatsLogo } from './StatsLogo'
import { StatsSection } from './StatsSection'
import { fmtMoney, useLocalStats } from './useLocalStats'

const DASH = '—'

/**
 * Presentational only — Strategy P&L, Efficiency, Hits/Rate, Shooter
 * net, and Net P&L stay "—" until something with real bet-resolution
 * and strategy tracking exists to feed them (Step 3+). Not fabricated
 * here, same rule the felt itself follows.
 */
export function StatsSidebar() {
  const stats = useLocalStats()
  const { sidebarRef, innerRef, height, scale } = useSidebarAutoFit()

  return (
    <div className="statsSidebar" id="statsSidebar" ref={sidebarRef} style={{ height }}>
      <div className="statsSidebarInner" id="statsSidebarInner" ref={innerRef} style={{ transform: `scale(${scale})` }}>
        <StatsLogo />
        <StatsSection
          title="Table Limits"
          defaultCollapsed={false}
          rows={[
            { label: 'Min', value: fmtMoney(stats.min) },
            { label: 'Max', value: fmtMoney(stats.max) },
            { label: 'Odds', value: stats.odds },
            { label: 'Odds max', value: fmtMoney(stats.oddsMax) },
          ]}
        />
        <StatsSection
          title="Current"
          defaultCollapsed={false}
          rows={[
            { label: 'Shooter', value: DASH },
            { label: 'Bets', value: String(stats.betsOn) },
            { label: 'Rack', value: fmtMoney(stats.rack) },
            { label: 'Bankroll', value: fmtMoney(stats.bankroll) },
          ]}
          netRow={{ label: 'Net', value: DASH }}
        />
        <StatsSection
          title="Session"
          defaultCollapsed={true}
          rows={[
            { label: 'Hands', value: String(stats.hands) },
            { label: 'Rolls', value: String(stats.rolls) },
            { label: 'Hits', value: DASH },
            { label: 'Rate', value: DASH },
          ]}
        />
        <DistributionSection distribution={stats.distribution} totalRolls={stats.rolls} />
        <StatsSection
          title="Efficiency"
          defaultCollapsed={true}
          rows={[
            { label: 'RPS', value: DASH },
            { label: 'AHL', value: DASH },
            { label: 'HPS', value: DASH },
            { label: 'BPS', value: DASH },
          ]}
        />
        <StatsSection
          title="Strategy"
          defaultCollapsed={true}
          rows={[
            { label: 'Across', value: DASH },
            { label: 'Inside', value: DASH },
            { label: 'Outside', value: DASH },
            { label: 'Horn', value: DASH },
          ]}
        />
      </div>
    </div>
  )
}
