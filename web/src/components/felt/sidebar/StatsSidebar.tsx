import { useSidebarAutoFit } from '../state/useSidebarAutoFit'
import { DistributionSection } from './DistributionSection'
import { StatsLogo } from './StatsLogo'
import { StatsSection } from './StatsSection'
import { fmtMoney, fmtSigned, useLocalStats } from './useLocalStats'

const DASH = '—'

/**
 * Presentational only — Table Limits, Efficiency, Hits/Rate stay "—"
 * (no HouseRules/strategy-coverage source exposed by the backend yet
 * — Step 3 is spectator-only, no new backend endpoints). Shooter and
 * Net come from FeltUiState (real in live mode via useFeltLiveState,
 * "—"-equivalent placeholders in dev mode).
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
          titleNode={
            stats.roster.length > 0 ? (
              <select className="stCurrentSelect" value={stats.selectedPlayer} onChange={(e) => stats.setSelectedPlayer(e.target.value)}>
                {stats.roster.map((p) => (
                  <option key={p.name} value={p.name}>
                    {p.name}
                  </option>
                ))}
              </select>
            ) : undefined
          }
          defaultCollapsed={false}
          rows={[
            { label: 'Shooter', value: stats.shooterName || DASH },
            { label: 'Bets', value: String(stats.betsOn) },
            { label: 'Rack', value: fmtMoney(stats.rack) },
            { label: 'Bankroll', value: fmtMoney(stats.bankroll) },
          ]}
          netRow={{ label: 'Net', value: stats.net === null ? DASH : fmtSigned(stats.net) }}
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
