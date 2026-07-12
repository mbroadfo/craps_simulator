import { useState } from 'react'

export interface StatRow {
  label: string
  value: string
  cls?: 'pos' | 'neg'
}

/**
 * One generic collapsible {title, rows[]} section — reused for Table
 * Limits/Current/Session/Efficiency/Strategy, which are all
 * structurally identical stRow lists (Distribution is genuinely
 * different markup — a histogram — and stays its own component).
 * Collapsed/expanded state is local: nothing outside this section
 * reads or writes it.
 */
export function StatsSection({ title, defaultCollapsed, rows, netRow }: { title: string; defaultCollapsed: boolean; rows: StatRow[]; netRow?: StatRow }) {
  const [collapsed, setCollapsed] = useState(defaultCollapsed)

  return (
    <div className={'stSection' + (collapsed ? ' collapsed' : '')} data-testid={`stats-section-${title}`}>
      <div className="stHeader" onClick={() => setCollapsed((v) => !v)}>
        <span className="stChevron">&#9662;</span>
        {title}
      </div>
      <div className="stBody">
        {rows.map((r) => (
          <div className="stRow" key={r.label}>
            <span className="stLabel">{r.label}</span>
            <span className={'stValue' + (r.cls ? ' ' + r.cls : '')}>{r.value}</span>
          </div>
        ))}
        {netRow && (
          <>
            <div className="stNetDivider" />
            <div className="stRow">
              <span className="stLabel">{netRow.label}</span>
              <span className={'stValue' + (netRow.cls ? ' ' + netRow.cls : '')}>{netRow.value}</span>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
