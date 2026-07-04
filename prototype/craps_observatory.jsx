import { useState, useEffect, useRef, useCallback } from "react";

// ============================================================
// THE RAIL — multi-table craps strategy observatory
// Prototype: 6 tables, 6 strategies, correct craps math.
// Pass line 1.41% edge, field 2.78% (12 pays triple),
// place 6/8 at 1.52%, true odds at 0%.
// ============================================================

const FELT = "#0E4232";
const FELT_DARK = "#0A2F24";
const BG = "#12100D";
const PANEL = "#1C1915";
const BONE = "#EFE7D3";
const CHIP_RED = "#C8412F";
const GOLD = "#D9A441";
const WIN = "#4CAF7D";
const LOSS = "#D95F4C";
const MUTED = "#8A8171";

const TABLE_MIN = 10;
const START_BANK = 1000;

// ---------- dice ----------
function rollDie() {
  return 1 + Math.floor(Math.random() * 6);
}

// ---------- payout helpers ----------
const PLACE_PAY = { 5: 7 / 5, 6: 7 / 6, 8: 7 / 6 };
const ODDS_PAY = { 4: 2, 5: 1.5, 6: 1.2, 8: 1.2, 9: 1.5, 10: 2 };
const ODDS_MULT = { 4: 3, 5: 4, 6: 5, 8: 5, 9: 4, 10: 3 }; // 3-4-5x

// ============================================================
// Strategies. Each is a pure-ish function: given table state,
// return the bets it WANTS on the layout before the next roll.
// The engine handles resolution. This narrow interface is the
// point — it's the contract an AI strategy generator writes to.
// ============================================================
const STRATEGIES = {
  passline: {
    name: "Pass Line Only",
    color: "#7FA6C9",
    desc: "The baseline. $10 pass, nothing else. House edge 1.41%.",
    wants(s) {
      return { pass: TABLE_MIN, odds: 0, place: {}, field: 0 };
    },
  },
  maxodds: {
    name: "Pass + 3-4-5x Odds",
    color: GOLD,
    desc: "Pass line with max free odds. Blended edge ~0.37%.",
    wants(s) {
      const odds = s.point ? TABLE_MIN * ODDS_MULT[s.point] : 0;
      return { pass: TABLE_MIN, odds, place: {}, field: 0 };
    },
  },
  place68: {
    name: "Place 6 & 8",
    color: "#B08BC9",
    desc: "$12 each on 6 and 8 when the point is on. Edge 1.52%.",
    wants(s) {
      return {
        pass: 0,
        odds: 0,
        place: s.point ? { 6: 12, 8: 12 } : {},
        field: 0,
      };
    },
  },
  ironcross: {
    name: "Iron Cross",
    color: CHIP_RED,
    desc: "Pass + place 5/6/8 + field. Every number but 7 pays.",
    wants(s) {
      return {
        pass: TABLE_MIN,
        odds: 0,
        place: s.point ? { 5: 10, 6: 12, 8: 12 } : {},
        field: s.point ? TABLE_MIN : 0,
      };
    },
  },
  fieldonly: {
    name: "Field Fanatic",
    color: "#C9A26B",
    desc: "$10 in the field, every roll, forever. Edge 2.78%.",
    wants(s) {
      return { pass: 0, odds: 0, place: {}, field: TABLE_MIN };
    },
  },
  regression: {
    name: "Regress & Press",
    color: WIN,
    desc: "Big 6/8 ($30), regress to $12 after one hit, down after two.",
    wants(s) {
      if (!s.point) return { pass: 0, odds: 0, place: {}, field: 0 };
      const hits = s.memo.hits || 0;
      if (hits === 0) return { pass: 0, odds: 0, place: { 6: 30, 8: 30 }, field: 0 };
      if (hits === 1) return { pass: 0, odds: 0, place: { 6: 12, 8: 12 }, field: 0 };
      return { pass: 0, odds: 0, place: {}, field: 0 }; // locked profit, sit out
    },
  },
};

const STRAT_KEYS = Object.keys(STRATEGIES);

// ============================================================
// Engine: one roll on one table. Mutates a copied state.
// ============================================================
function freshTable(stratKey, id) {
  return {
    id,
    stratKey,
    bankroll: START_BANK,
    point: null,
    dice: [3, 4],
    rolls: 0,
    pnlFlash: 0,
    busted: false,
    peak: START_BANK,
    maxDD: 0,
    wagered: 0,
    memo: {},
    spark: [START_BANK],
    bets: { pass: 0, odds: 0, place: {}, field: 0 },
  };
}

function doRoll(t) {
  if (t.busted) return t;
  const strat = STRATEGIES[t.stratKey];

  // 1. Strategy declares desired layout; engine funds the delta.
  const want = strat.wants(t);
  let cost = 0;
  const bets = { ...t.bets, place: { ...t.bets.place } };

  if (want.pass > bets.pass && !t.point) {
    cost += want.pass - bets.pass;
    bets.pass = want.pass;
  }
  if (want.odds > bets.odds && t.point && bets.pass > 0) {
    cost += want.odds - bets.odds;
    bets.odds = want.odds;
  }
  for (const n of [5, 6, 8]) {
    const w = want.place[n] || 0;
    const h = bets.place[n] || 0;
    if (w > h) {
      cost += w - h;
      bets.place[n] = w;
    } else if (w < h) {
      // regression: take down, return to bankroll
      cost -= h - w;
      if (w === 0) delete bets.place[n];
      else bets.place[n] = w;
    }
  }
  if (want.field > 0) {
    cost += want.field;
    bets.field = want.field;
  }

  if (cost > t.bankroll) {
    // can't fund the layout — go flat, ride what's out there
    if (t.bankroll <= 0 && bets.pass === 0 && Object.keys(bets.place).length === 0) {
      return { ...t, busted: true };
    }
  } else {
    t = { ...t, bankroll: t.bankroll - cost, wagered: t.wagered + Math.max(cost, 0) };
  }

  // 2. Roll.
  const d1 = rollDie(), d2 = rollDie();
  const sum = d1 + d2;
  let delta = 0;
  let point = t.point;
  const memo = { ...t.memo };

  // 3. Field (one-roll, always working).
  if (bets.field > 0) {
    if ([3, 4, 9, 10, 11].includes(sum)) delta += bets.field * 2; // stake + 1:1
    else if (sum === 2) delta += bets.field * 3; // 2:1
    else if (sum === 12) delta += bets.field * 4; // 3:1
    bets.field = 0; // resolved either way
  }

  // 4. Place bets (off on comeout).
  if (point) {
    if (sum === 7) {
      bets.place = {};
      memo.hits = 0;
    } else if (bets.place[sum]) {
      delta += bets.place[sum] * PLACE_PAY[sum]; // winnings only, bet stays up
      memo.hits = (memo.hits || 0) + 1;
    }
  }

  // 5. Pass line + odds.
  if (!point) {
    if (bets.pass > 0) {
      if (sum === 7 || sum === 11) delta += bets.pass * 2;
      else if ([2, 3, 12].includes(sum)) bets.pass = 0;
    }
    if (![2, 3, 7, 11, 12].includes(sum)) {
      point = sum;
      memo.hits = 0;
    } else if (sum === 7 || sum === 11) {
      bets.pass = 0; // paid out above, cleared for re-bet
    }
  } else {
    if (sum === point) {
      if (bets.pass > 0) delta += bets.pass * 2;
      if (bets.odds > 0) delta += bets.odds + bets.odds * ODDS_PAY[point];
      bets.pass = 0;
      bets.odds = 0;
      point = null;
      memo.hits = 0;
    } else if (sum === 7) {
      bets.pass = 0;
      bets.odds = 0;
      point = null;
      memo.hits = 0;
    }
  }

  const bankroll = t.bankroll + delta;
  const peak = Math.max(t.peak, bankroll);
  const maxDD = Math.max(t.maxDD, peak - bankroll);
  const spark = [...t.spark.slice(-119), bankroll];
  const busted = bankroll < TABLE_MIN && Object.keys(bets.place).length === 0 && bets.pass === 0;

  return {
    ...t,
    dice: [d1, d2],
    point,
    bets,
    memo,
    bankroll,
    peak,
    maxDD,
    spark,
    busted,
    rolls: t.rolls + 1,
    pnlFlash: delta > cost ? 1 : delta === 0 && cost > 0 ? -1 : 0,
  };
}

// ============================================================
// Visual components
// ============================================================
const PIPS = {
  1: [4], 2: [0, 8], 3: [0, 4, 8], 4: [0, 2, 6, 8], 5: [0, 2, 4, 6, 8], 6: [0, 2, 3, 5, 6, 8],
};

function Die({ value }) {
  return (
    <div
      className="grid grid-cols-3 grid-rows-3 rounded"
      style={{
        width: 26, height: 26, padding: 3, gap: 1,
        background: BONE, boxShadow: "0 2px 3px rgba(0,0,0,.5), inset 0 -2px 0 rgba(0,0,0,.15)",
      }}
    >
      {Array.from({ length: 9 }).map((_, i) => (
        <div key={i} className="flex items-center justify-center">
          {PIPS[value].includes(i) && (
            <div style={{ width: 4, height: 4, borderRadius: 99, background: "#20180F" }} />
          )}
        </div>
      ))}
    </div>
  );
}

function Spark({ data, color }) {
  const w = 220, h = 34;
  const min = Math.min(...data), max = Math.max(...data);
  const span = Math.max(max - min, 1);
  const pts = data
    .map((v, i) => `${(i / Math.max(data.length - 1, 1)) * w},${h - ((v - min) / span) * (h - 4) - 2}`)
    .join(" ");
  const baseY = h - ((START_BANK - min) / span) * (h - 4) - 2;
  return (
    <svg width="100%" height={h} viewBox={`0 0 ${w} ${h}`} preserveAspectRatio="none">
      {START_BANK >= min && START_BANK <= max && (
        <line x1="0" y1={baseY} x2={w} y2={baseY} stroke={MUTED} strokeWidth="0.5" strokeDasharray="3 3" opacity="0.5" />
      )}
      <polyline points={pts} fill="none" stroke={color} strokeWidth="1.6" strokeLinejoin="round" />
    </svg>
  );
}

const BOX_NUMS = [4, 5, 6, 8, 9, 10];

function TableCard({ t }) {
  const strat = STRATEGIES[t.stratKey];
  const pnl = t.bankroll - START_BANK;
  const flashColor = t.pnlFlash > 0 ? WIN : t.pnlFlash < 0 ? LOSS : "transparent";
  return (
    <div
      className="rounded-lg overflow-hidden flex flex-col"
      style={{
        background: PANEL,
        border: `1px solid ${t.busted ? LOSS : "#2A251E"}`,
        boxShadow: `0 0 0 1px transparent, 0 0 18px ${flashColor}22`,
        transition: "box-shadow .25s",
        opacity: t.busted ? 0.55 : 1,
      }}
    >
      {/* header */}
      <div className="flex items-center justify-between px-3 pt-2 pb-1">
        <div className="flex items-center gap-2 min-w-0">
          <div style={{ width: 8, height: 8, borderRadius: 99, background: strat.color, flexShrink: 0 }} />
          <span className="truncate" style={{ fontFamily: "'Barlow Condensed', sans-serif", fontSize: 17, fontWeight: 600, letterSpacing: ".04em", color: BONE, textTransform: "uppercase" }}>
            {strat.name}
          </span>
        </div>
        {t.busted ? (
          <span style={{ color: LOSS, fontFamily: "'IBM Plex Mono', monospace", fontSize: 11, fontWeight: 700 }}>BUSTED</span>
        ) : (
          <span style={{ fontFamily: "'IBM Plex Mono', monospace", fontSize: 12, color: pnl >= 0 ? WIN : LOSS }}>
            {pnl >= 0 ? "+" : "−"}${Math.abs(pnl).toFixed(0)}
          </span>
        )}
      </div>

      {/* felt */}
      <div className="mx-3 rounded-md relative" style={{ background: `radial-gradient(ellipse at 50% 0%, ${FELT}, ${FELT_DARK})`, border: "1px solid #0A241B", padding: "8px 10px 10px" }}>
        {/* box numbers + puck */}
        <div className="flex justify-between mb-2">
          {BOX_NUMS.map((n) => (
            <div key={n} className="relative flex flex-col items-center" style={{ width: 26 }}>
              <div
                className="flex items-center justify-center rounded-sm"
                style={{
                  width: 24, height: 20, fontFamily: "'IBM Plex Mono', monospace", fontSize: 11, fontWeight: 700,
                  color: t.point === n ? "#20180F" : BONE,
                  background: t.point === n ? BONE : "rgba(0,0,0,.25)",
                  border: `1px solid ${t.point === n ? BONE : "#1C5A44"}`,
                }}
              >
                {n}
              </div>
              {t.bets.place[n] > 0 && (
                <div
                  className="flex items-center justify-center rounded-full mt-1"
                  style={{
                    width: 18, height: 18, fontSize: 8, fontWeight: 700, color: BONE,
                    background: CHIP_RED, border: `1.5px dashed ${BONE}`, fontFamily: "'IBM Plex Mono', monospace",
                  }}
                >
                  {t.bets.place[n]}
                </div>
              )}
            </div>
          ))}
        </div>

        {/* dice + line bets */}
        <div className="flex items-center justify-between">
          <div className="flex gap-1.5">
            <Die value={t.dice[0]} />
            <Die value={t.dice[1]} />
          </div>
          <div className="flex gap-2" style={{ fontFamily: "'IBM Plex Mono', monospace", fontSize: 10, color: "#9BC4AE" }}>
            {t.bets.pass > 0 && <span>PASS ${t.bets.pass}</span>}
            {t.bets.odds > 0 && <span>ODDS ${t.bets.odds}</span>}
            {!t.point && <span style={{ color: MUTED }}>COME OUT</span>}
          </div>
        </div>
      </div>

      {/* bankroll + sparkline */}
      <div className="px-3 pt-1.5 pb-2">
        <div className="flex items-baseline justify-between">
          <span style={{ fontFamily: "'IBM Plex Mono', monospace", fontSize: 15, color: BONE }}>
            ${t.bankroll.toFixed(0)}
          </span>
          <span style={{ fontFamily: "'IBM Plex Mono', monospace", fontSize: 10, color: MUTED }}>
            {t.rolls.toLocaleString()} rolls
          </span>
        </div>
        <Spark data={t.spark} color={strat.color} />
      </div>
    </div>
  );
}

// ============================================================
// App
// ============================================================
const SPEEDS = [
  { label: "1×", interval: 700, batch: 1 },
  { label: "10×", interval: 180, batch: 2 },
  { label: "100×", interval: 60, batch: 6 },
  { label: "TURBO", interval: 40, batch: 60 },
];

export default function CrapsObservatory() {
  const [tables, setTables] = useState(() => STRAT_KEYS.map((k, i) => freshTable(k, i)));
  const [running, setRunning] = useState(false);
  const [speedIdx, setSpeedIdx] = useState(1);
  const timer = useRef(null);

  const tick = useCallback((batch) => {
    setTables((prev) =>
      prev.map((t) => {
        let nt = t;
        for (let i = 0; i < batch; i++) nt = doRoll(nt);
        return nt;
      })
    );
  }, []);

  useEffect(() => {
    if (!running) return;
    const { interval, batch } = SPEEDS[speedIdx];
    timer.current = setInterval(() => tick(batch), interval);
    return () => clearInterval(timer.current);
  }, [running, speedIdx, tick]);

  const reset = () => {
    setRunning(false);
    setTables(STRAT_KEYS.map((k, i) => freshTable(k, i)));
  };

  const totalRolls = tables.reduce((a, t) => a + t.rolls, 0);
  const ranked = [...tables].sort((a, b) => b.bankroll - a.bankroll);

  return (
    <div className="min-h-screen w-full" style={{ background: BG, color: BONE }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@500;600;700&family=IBM+Plex+Mono:wght@400;700&display=swap');
      `}</style>

      {/* header */}
      <div className="flex flex-wrap items-center justify-between gap-3 px-5 py-4" style={{ borderBottom: "1px solid #2A251E" }}>
        <div>
          <h1 style={{ fontFamily: "'Barlow Condensed', sans-serif", fontSize: 30, fontWeight: 700, letterSpacing: ".08em", lineHeight: 1, textTransform: "uppercase" }}>
            The <span style={{ color: GOLD }}>Rail</span>
          </h1>
          <p style={{ fontFamily: "'IBM Plex Mono', monospace", fontSize: 10, color: MUTED, marginTop: 4 }}>
            strategy observatory {"·"} {totalRolls.toLocaleString()} rolls thrown
          </p>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex rounded overflow-hidden" style={{ border: "1px solid #2A251E" }}>
            {SPEEDS.map((s, i) => (
              <button
                key={s.label}
                onClick={() => setSpeedIdx(i)}
                className="px-3 py-1.5"
                style={{
                  fontFamily: "'IBM Plex Mono', monospace", fontSize: 11, fontWeight: 700,
                  background: i === speedIdx ? GOLD : "transparent",
                  color: i === speedIdx ? "#20180F" : MUTED, cursor: "pointer", border: "none",
                }}
              >
                {s.label}
              </button>
            ))}
          </div>
          <button
            onClick={() => setRunning((r) => !r)}
            className="px-4 py-1.5 rounded"
            style={{
              fontFamily: "'Barlow Condensed', sans-serif", fontSize: 15, fontWeight: 700, letterSpacing: ".08em",
              background: running ? "transparent" : WIN, color: running ? WIN : "#0A2F24",
              border: `1px solid ${WIN}`, cursor: "pointer", textTransform: "uppercase",
            }}
          >
            {running ? "Pause" : "Roll"}
          </button>
          <button
            onClick={reset}
            className="px-3 py-1.5 rounded"
            style={{
              fontFamily: "'Barlow Condensed', sans-serif", fontSize: 15, fontWeight: 600, letterSpacing: ".08em",
              background: "transparent", color: MUTED, border: "1px solid #2A251E", cursor: "pointer", textTransform: "uppercase",
            }}
          >
            Reset
          </button>
        </div>
      </div>

      {/* tables */}
      <div className="grid gap-3 p-4 sm:grid-cols-2 lg:grid-cols-3">
        {tables.map((t) => <TableCard key={t.id} t={t} />)}
      </div>

      {/* leaderboard */}
      <div className="px-4 pb-6">
        <h2 style={{ fontFamily: "'Barlow Condensed', sans-serif", fontSize: 18, fontWeight: 600, letterSpacing: ".1em", color: MUTED, textTransform: "uppercase", marginBottom: 8 }}>
          Leaderboard
        </h2>
        <div className="rounded-lg overflow-x-auto" style={{ border: "1px solid #2A251E" }}>
          <table className="w-full" style={{ fontFamily: "'IBM Plex Mono', monospace", fontSize: 12, borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ color: MUTED, background: PANEL }}>
                {["#", "Strategy", "Bankroll", "P&L", "Rolls", "Max Drawdown", "Realized Edge"].map((h) => (
                  <th key={h} className="text-left px-3 py-2" style={{ fontWeight: 400, whiteSpace: "nowrap" }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {ranked.map((t, i) => {
                const strat = STRATEGIES[t.stratKey];
                const pnl = t.bankroll - START_BANK;
                const edge = t.wagered > 0 ? (pnl / t.wagered) * 100 : 0;
                return (
                  <tr key={t.id} style={{ borderTop: "1px solid #2A251E" }}>
                    <td className="px-3 py-2" style={{ color: MUTED }}>{i + 1}</td>
                    <td className="px-3 py-2" style={{ whiteSpace: "nowrap" }}>
                      <span style={{ color: strat.color }}>{"●"}</span>{" "}
                      <span style={{ color: BONE }}>{strat.name}</span>
                      {t.busted && <span style={{ color: LOSS }}> {"†"}</span>}
                    </td>
                    <td className="px-3 py-2" style={{ color: BONE }}>${t.bankroll.toFixed(0)}</td>
                    <td className="px-3 py-2" style={{ color: pnl >= 0 ? WIN : LOSS }}>
                      {pnl >= 0 ? "+" : "−"}${Math.abs(pnl).toFixed(0)}
                    </td>
                    <td className="px-3 py-2" style={{ color: MUTED }}>{t.rolls.toLocaleString()}</td>
                    <td className="px-3 py-2" style={{ color: MUTED }}>{"−"}${t.maxDD.toFixed(0)}</td>
                    <td className="px-3 py-2" style={{ color: edge >= 0 ? WIN : LOSS }}>{edge.toFixed(2)}%</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        <p style={{ fontFamily: "'IBM Plex Mono', monospace", fontSize: 10, color: MUTED, marginTop: 8 }}>
          Realized edge converges on theory as rolls climb: pass {"−"}1.41% {"·"} 3-4-5x odds {"−"}0.37% {"·"} place 6/8 {"−"}1.52% {"·"} field {"−"}2.78%. Run TURBO and watch the math win.
        </p>
      </div>
    </div>
  );
}
