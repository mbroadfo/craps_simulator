import { DENOMS } from '../data'
import { CHIP_H, CHIP_PATTERNS, CHIP_PITCH, CHIP_W, GROUP_GAP, RAIL_H, RAIL_ORDER, RAIL_W, RAIL_X0, RAIL_Y0 } from '../layout'
import { useFeltState } from '../state/FeltStateContext'

// Wood body + one groove — the felt only ever shows one seat's rack
// (single-player, see phase2-table-fidelity memory), so a second row
// never had anything to hold; it just sat empty. Tighter corner radii
// and a subdued inset-shadow overlay on the groove read less like a
// toy and more like carved wood. Single-use (only ChipRail calls it),
// stays local.
function RailChrome({ x, y, w, h }: { x: number; y: number; w: number; h: number }) {
  return (
    <>
      <rect x={x} y={y} width={w} height={h} rx={5} fill="url(#railWood)" />
      <rect x={x} y={y} width={w} height={h} rx={5} fill="none" stroke="#a07030" strokeWidth={1} strokeOpacity={0.35} />
      <rect x={x + 8} y={y + 5} width={w - 16} height={h - 10} rx={3} fill="#241207" />
      <rect x={x + 8} y={y + 5} width={w - 16} height={h - 10} rx={3} fill="url(#grooveShade)" />
    </>
  )
}

// A chip standing on edge, drawn as a slim rectangle (not an ellipse) —
// real chip stock is flat, and from the side it reads as a thin bar,
// not a lens shape. Body cream, with 7 stacked bands alternating
// color/white per CHIP_PATTERNS. Chips lie flat against their
// neighbors — no per-chip tilt — only which band run they show varies.
function ChipRect({ cx, cy, fill, index, onClick }: { cx: number; cy: number; fill: string; index: number; onClick: () => void }) {
  const pattern = CHIP_PATTERNS[index % CHIP_PATTERNS.length]
  const bandH = CHIP_H / pattern.length
  return (
    <g transform={`translate(${cx},${cy})`} style={{ cursor: 'pointer' }}>
      <rect x={-CHIP_W / 2} y={-CHIP_H / 2} width={CHIP_W} height={CHIP_H} rx={1.3} fill="#f0ebdc" />
      {pattern.map(
        (band, i) => band === 'c' && <rect key={i} x={-CHIP_W / 2} y={-CHIP_H / 2 + i * bandH} width={CHIP_W} height={bandH} fill={fill} />,
      )}
      <rect x={-CHIP_W / 2} y={-CHIP_H / 2} width={CHIP_W} height={CHIP_H} rx={1.3} fill="none" stroke="#00000060" strokeWidth={0.75} />
      <rect x={-CHIP_W / 2 - 2} y={-CHIP_H / 2 - 2} width={CHIP_W + 4} height={CHIP_H + 4} fill="transparent" onClick={onClick} />
    </g>
  )
}

/**
 * The physical chip rail below the felt (drawChipRail in the
 * prototype) — horizontal, right-justified to the table's own right
 * edge. Live: clicking a chip selects its denomination (felt clicks
 * then spend from this rack via FeltStateContext).
 */
export function ChipRail() {
  const { rack, selectedDenom, setSelectedDenom } = useFeltState()
  const groups = RAIL_ORDER.map((v) => ({ value: v, count: rack[v] || 0 })).filter((gr) => gr.count > 0)

  let x = RAIL_X0 + 14
  let chipIndex = 0

  return (
    <g id="rail-section-P1" data-testid="chip-rail">
      <RailChrome x={RAIL_X0} y={RAIL_Y0} w={RAIL_W} h={RAIL_H} />
      {groups.map((gr) => {
        const groupW = gr.count * CHIP_PITCH - (CHIP_PITCH - CHIP_W)
        const groupX = x
        const fill = DENOMS.find((d) => d.value === gr.value)!.fill
        const chips = []
        for (let i = 0; i < gr.count; i++) {
          chips.push(<ChipRect key={chipIndex} cx={x + CHIP_W / 2} cy={RAIL_Y0 + RAIL_H / 2} fill={fill} index={chipIndex} onClick={() => setSelectedDenom(gr.value)} />)
          chipIndex++
          x += CHIP_PITCH
        }
        x += GROUP_GAP - (CHIP_PITCH - CHIP_W)
        return (
          <g key={gr.value}>
            {gr.value === selectedDenom && <circle cx={groupX + groupW / 2} cy={RAIL_Y0 + RAIL_H - 10} r={4.5} fill="#c9a84c" />}
            {chips}
          </g>
        )
      })}
    </g>
  )
}
