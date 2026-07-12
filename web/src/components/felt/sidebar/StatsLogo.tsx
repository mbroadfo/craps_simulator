// "The Pit" wordmark — two dice showing 11 (5+6) beside the name.
// Georgia italic script, same voice as the felt's own "Come" — a
// deliberate brand mark, not part of the data-font decision the rest
// of the sidebar uses (Barlow).
export function StatsLogo() {
  return (
    <div className="stLogo">
      <svg viewBox="0 0 140 60" xmlns="http://www.w3.org/2000/svg" aria-label="The Pit — dice showing 11">
        {/* die showing 5 */}
        <rect x={40} y={4} width={28} height={28} rx={4} fill="#efe7d3" stroke="#20180f" strokeWidth={1.5} />
        <circle cx={47} cy={11} r={2.4} fill="#20180f" />
        <circle cx={61} cy={11} r={2.4} fill="#20180f" />
        <circle cx={54} cy={18} r={2.4} fill="#20180f" />
        <circle cx={47} cy={25} r={2.4} fill="#20180f" />
        <circle cx={61} cy={25} r={2.4} fill="#20180f" />
        {/* die showing 6 */}
        <rect x={72} y={4} width={28} height={28} rx={4} fill="#efe7d3" stroke="#20180f" strokeWidth={1.5} />
        <circle cx={79} cy={11} r={2.4} fill="#20180f" />
        <circle cx={93} cy={11} r={2.4} fill="#20180f" />
        <circle cx={79} cy={18} r={2.4} fill="#20180f" />
        <circle cx={93} cy={18} r={2.4} fill="#20180f" />
        <circle cx={79} cy={25} r={2.4} fill="#20180f" />
        <circle cx={93} cy={25} r={2.4} fill="#20180f" />
        <text x={70} y={50} textAnchor="middle" fontFamily="Georgia, 'Times New Roman', serif" fontStyle="italic" fontWeight={700} fontSize={19} letterSpacing={0.5} fill="#c9a84c">
          The Pit
        </text>
      </svg>
    </div>
  )
}
