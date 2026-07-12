// <defs> gradients ported verbatim from prototype/parametric-felt.html.
export function FeltDefs() {
  return (
    <defs>
      <radialGradient id="felt-bg" cx="42%" cy="42%" r="78%" gradientUnits="objectBoundingBox">
        <stop offset="0%" stopColor="#121317" />
        <stop offset="100%" stopColor="#07080a" />
      </radialGradient>
      <linearGradient id="ember" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stopColor="#f3ce74" />
        <stop offset="55%" stopColor="#e8a04a" />
        <stop offset="100%" stopColor="#d9622b" />
      </linearGradient>
      <linearGradient id="ember-soft" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stopColor="#d4873a" />
        <stop offset="100%" stopColor="#c9a84c" />
      </linearGradient>
      <linearGradient id="railWood" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stopColor="#6b4423" />
        <stop offset="45%" stopColor="#5c3a1e" />
        <stop offset="100%" stopColor="#432914" />
      </linearGradient>
      <linearGradient id="grooveShade" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stopColor="#000000" stopOpacity="0.7" />
        <stop offset="18%" stopColor="#000000" stopOpacity="0.15" />
        <stop offset="82%" stopColor="#000000" stopOpacity="0" />
        <stop offset="100%" stopColor="#ffffff" stopOpacity="0.12" />
      </linearGradient>
    </defs>
  )
}
