import { useState } from 'react'
import { DenomPicker } from '../chips/DenomPicker'
import { useFeltState } from '../state/FeltStateContext'

/**
 * Denom picker + Roll/Clear buttons (the prototype's .actionBar).
 * Roll is a genuine random 2d6 roller (rollDice, no bet-resolution
 * logic — out of scope for this prototype); Clear returns the felt's
 * chips to the rack. Shooter reset used to live as its own button in
 * the dev-controls panel (redundant with Roll, which is already
 * here) — it's a "…" expand next to Clear instead, so resetting the
 * shooter doesn't need a trip to the hamburger menu.
 */
export function ActionBar() {
  const { rollDice, clearAllBets, resetShooter } = useFeltState()
  const [showReset, setShowReset] = useState(false)

  return (
    <div className="actionBar">
      <DenomPicker />
      <div className="btnRow">
        <button id="rollBtn" className="rollBtn" title="Roll — random 2d6, tracks point/seven-out" onClick={rollDice}>
          <svg viewBox="0 0 46 46" width="46" height="46">
            <defs>
              <radialGradient id="rollBtnGrad" cx="35%" cy="28%" r="75%">
                <stop offset="0%" stopColor="#ea5b48" />
                <stop offset="55%" stopColor="#b3271c" />
                <stop offset="100%" stopColor="#7a1712" />
              </radialGradient>
            </defs>
            <circle cx={23} cy={23} r={21} fill="url(#rollBtnGrad)" stroke="#c9a84c" strokeWidth={2.5} />
            <circle cx={23} cy={23} r={21} fill="none" stroke="#5a120c" strokeWidth={1} strokeOpacity={0.5} />
            <ellipse cx={18} cy={14} rx={10.5} ry={5.5} fill="#ffffff" fillOpacity={0.22} />
            <text
              x={23}
              y={28}
              textAnchor="middle"
              fontFamily="Arial, Helvetica, sans-serif"
              fontWeight={800}
              fontSize={12}
              letterSpacing={0.5}
              fill="#ffffff"
              stroke="#5a120c"
              strokeWidth={1.6}
              style={{ paintOrder: 'stroke fill' }}
            >
              ROLL
            </text>
          </svg>
        </button>
        <button id="clearBtn" className="iconBtn" title="Clear all bets" onClick={clearAllBets}>
          <svg viewBox="0 0 32 32" width="38" height="38">
            <path d="M 10,1 L 22,1 L 22,13 L 28,13 L 16,29 L 4,13 L 10,13 Z" fill="#f3ce74" stroke="#7a5c14" strokeWidth={1.2} />
            <text x={16} y={20.5} textAnchor="middle" fontFamily="Arial, Helvetica, sans-serif" fontWeight={800} fontSize={13} fill="#14100a">
              $
            </text>
          </svg>
        </button>
        <button className="iconBtn" title="More" aria-expanded={showReset} onClick={() => setShowReset((v) => !v)}>
          &hellip;
        </button>
        {showReset && (
          <button
            className="iconBtn"
            title="Reset shooter — clears roll history, point off"
            onClick={() => {
              resetShooter()
              setShowReset(false)
            }}
          >
            &#8635;
          </button>
        )}
      </div>
    </div>
  )
}
