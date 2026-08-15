/**
 * The real thing (Step 3 + 3b + 3c + Observatory panel): build a
 * lineup in the Observatory panel's checkbox list, then Start the
 * table from ControlRail — a fixed, always-visible action bar (see
 * ObservatoryPanel.tsx). Starting does not set the game rolling by
 * itself: it lands paused, and from there the game only ever
 * progresses via that same Start/Roll button (single step), the
 * separate Autoplay toggle, or Turbo, all in that same rail. Watch it play
 * out on the faithful felt — chips, toasts, shooter history, and now
 * an animated pair of dice (Phase A — see components/felt/dice/) that
 * fly/tumble/bounce/settle before a roll's chip movement, fade-ups,
 * or ATS-lit numbers become visible: DiceRolled envelopes (and
 * everything that follows until the animation settles) are queued in
 * `pendingEnvelopes` rather than applied immediately — see attach()
 * and handleDiceSettled below. Alongside a bot roster with sparklines
 * for switching perspective, a leaderboard, a roll-distribution
 * chart, a roll feed, and a full-height session graph to scroll down
 * to. The old ControlStripe/PlayerSidebar pair is gone, folded into
 * the Observatory panel.
 */
import { useCallback, useEffect, useRef, useState } from 'react'

import type { DiceAnimationHandle } from './components/felt/dice/DiceAnimation'
import { LiveFelt } from './components/felt/Felt'
import { initialRollLogState, rollLogReducer, type RollLogState } from './components/felt/state/liveRollLog'
import { initialPlayByPlay, playByPlayReducer, type PlayByPlayEntry } from './components/felt/state/playByPlay'
import { netFor } from './components/felt/state/useFeltLiveState'
import type { RosterEntry } from './components/felt/types'
import type { ObsPlayerRow } from './components/observatorypanel/BotRoster'
import { MAX_SPEED } from './components/observatorypanel/ControlRail'
import { ObservatoryPanel, type Seat } from './components/observatorypanel/ObservatoryPanel'
import { SessionGraph, type GraphPlayer } from './components/sessiongraph/SessionGraph'
import { api, type TableSnapshot } from './lib/api'
import type { Envelope } from './lib/events'
import { connectTableStream, type StreamHandle } from './lib/sse'
import { initialState, tableReducer, type TableState } from './lib/tableReducer'

const DEFAULT_ROLL_DELAY_MS = 500
const DEFAULT_NUM_SHOOTERS = 10
// How long a just-resolved round's toasts stay on screen alone before
// the next round's bets/commentary are revealed — see handleDiceSettled.
const REVEAL_DELAY_MS = 500

// Seats are keyed by strategy name, one-to-one — the player *name*
// sent to the backend is just the strategy name too (PlayerSpec still
// carries name/strategy as separate fields, so this is free to change
// later without a data-model migration).
const DEFAULT_CHECKED = new Set(['Pass-Line', 'Iron Cross', '3-Point Molly'])

// Qualitative palette for per-player graph lines — distinct hues, not
// tied to any win/loss meaning (unlike the felt's own red/green).
const PLAYER_COLORS = ['#4a7fd4', '#e8a04a', '#2ecc71', '#d95f4c', '#9b6fd1', '#4fd1c5', '#e0c341', '#c9a84c']

export default function App() {
  const [snapshot, setSnapshot] = useState<TableSnapshot | null>(null)
  const [state, setState] = useState<TableState>(initialState)
  const [rollLog, setRollLog] = useState<RollLogState>(initialRollLogState)
  const [feed, setFeed] = useState<PlayByPlayEntry[]>(initialPlayByPlay)
  const [playerName, setPlayerName] = useState<string>('')
  const [speed, setSpeed] = useState(1)
  const [numShooters, setNumShooters] = useState(DEFAULT_NUM_SHOOTERS)
  const [seats, setSeats] = useState<Seat[]>([])
  const [creating, setCreating] = useState(false)
  const [error, setError] = useState<string | null>(null)
  // Not React state: DiceAnimation is fed each roll via this ref's
  // imperative enqueue() call, not a prop — see DiceAnimation's own
  // docstring for why a `result` prop (driven by setState) used to
  // silently lose rolls under React's batching whenever the backend
  // outpaced a render (routine at Turbo, and possible at any speed
  // once enough backlog piles up).
  const diceAnimationRef = useRef<DiceAnimationHandle>(null)
  const stream = useRef<StreamHandle | null>(null)
  // While the dice animation plays, envelopes that would move chips,
  // pop fade-up toasts, or light ATS numbers are queued here instead
  // of applied — see handleDiceSettled, which flushes them once
  // DiceAnimation reports the roll has landed (dice/DiceAnimation.tsx).
  const diceAnimating = useRef(false)
  const pendingEnvelopes = useRef<Envelope[]>([])

  // The two-phase roll cycle: the backend now publishes a round's bets
  // (BetPlaced/BetStatusChanged, capped off by RoundReady) strictly
  // *before* that round's own DiceRolled — see table_session.py's
  // _drive(), which calls prepare_next_roll() ungated at the top of
  // its loop and roll_and_resolve() only once the pause gate/pace
  // allow it. The felt should hold those next-round envelopes back
  // until the *current* round's animation has fully settled AND an
  // extra ~500ms has passed (so the win/loss toasts actually get seen
  // before new chips land on top of them) — a second, later gate than
  // diceAnimating/pendingEnvelopes above, which only covers the
  // current round's own resolution.
  //
  // BetsRequested (published as the very first thing inside
  // accept_bets()) marks the moment envelopes stop being "this round's
  // resolution" and start being "next round's prep"; the following
  // DiceRolled marks the end of prep and the start of a new round's
  // resolution. inPrepPhase tracks which side of that boundary we're
  // on; awaitingReveal opens the instant DiceRolled arrives (not later,
  // at settle) so envelopes are guaranteed to queue no matter how fast
  // the backend or how slow the animation.
  const awaitingReveal = useRef(false)
  const inPrepPhase = useRef(false)
  const revealQueue = useRef<Envelope[]>([])
  const revealTimer = useRef<number | null>(null)
  const [awaitingRoll, setAwaitingRoll] = useState(false)

  // Dealer-call speech bubble (Observatory panel roster, Tier 1) — the
  // active shooter's static come-out line, auto-hides after 3s. A ref,
  // not state, for the lookup table: attach()'s SSE callback is a
  // useCallback created once with `[applyAndUnlockRoll]` as its only
  // dep, so reading a live useState here would close over a permanently-stale
  // empty value (same reason diceAnimating/pendingEnvelopes are refs).
  const strategyDealerCalls = useRef<Record<string, string>>({})
  const [activeShooterCall, setActiveShooterCall] = useState<{ name: string; text: string } | null>(null)
  const activeShooterTimer = useRef<number | null>(null)
  // Persists for the shooter's whole turn (unlike activeShooterCall,
  // which clears after 3s) — PointHit carries no player identity of
  // its own, so this is how a re-announcement on PointHit knows who
  // to re-announce for.
  const currentShooterName = useRef<string | null>(null)

  // Lifted out of ObservatoryPanel (rather than local state there) so
  // ControlRail's Start button can read the current lineup selection
  // too — see ObservatoryPanel.tsx's header comment.
  useEffect(() => {
    api.listStrategies().then((list) => {
      setSeats(list.map((s) => ({ name: s.name, enabled: DEFAULT_CHECKED.has(s.name) })))
      strategyDealerCalls.current = Object.fromEntries(list.map((s) => [s.name, s.dealer_call]))
    })
  }, [])

  const handleToggleSeat = useCallback((index: number) => {
    setSeats((prev) => prev.map((s, i) => (i === index ? { ...s, enabled: !s.enabled } : s)))
  }, [])
  const handleSelectAll = useCallback(() => setSeats((prev) => prev.map((s) => ({ ...s, enabled: true }))), [])
  const handleClearAll = useCallback(() => setSeats((prev) => prev.map((s) => ({ ...s, enabled: false }))), [])

  const applyEnvelope = useCallback((envelope: Envelope) => {
    setState((s) => tableReducer(s, envelope))
    setRollLog((l) => rollLogReducer(l, envelope))
    setFeed((f) => playByPlayReducer(f, envelope))
  }, [])

  // applyEnvelope, plus: a RoundReady is the signal that this round's
  // bets are fully revealed and it's safe to roll again — shared by
  // both places an envelope can apply immediately (attach()'s SSE
  // callback, when nothing is queued) and where a held-back batch
  // finally applies (flushOneRoundOfReveal).
  const applyAndUnlockRoll = useCallback(
    (envelope: Envelope) => {
      applyEnvelope(envelope)
      if (envelope.type === 'RoundReady') setAwaitingRoll(false)
    },
    [applyEnvelope],
  )

  const attach = useCallback(
    (tableId: string) => {
      stream.current?.close()
      setState(initialState())
      setRollLog(initialRollLogState())
      setFeed(initialPlayByPlay())
      diceAnimating.current = false
      pendingEnvelopes.current = []
      diceAnimationRef.current?.reset()
      awaitingReveal.current = false
      inPrepPhase.current = false
      revealQueue.current = []
      if (revealTimer.current) window.clearTimeout(revealTimer.current)
      revealTimer.current = null
      setAwaitingRoll(false)
      if (activeShooterTimer.current) window.clearTimeout(activeShooterTimer.current)
      activeShooterTimer.current = null
      setActiveShooterCall(null)
      currentShooterName.current = null

      // Shared by both ShooterAssigned and PointHit below — a shooter's
      // "opening call" belongs to every come-out roll of their turn,
      // not just the first one: after they make their point they keep
      // the dice and start a fresh come-out sequence (PointHit is that
      // moment), so the call re-announces there too, not only once per
      // ShooterAssigned.
      const showDealerCall = (name: string) => {
        const call = strategyDealerCalls.current[name]
        if (!call) return
        if (activeShooterTimer.current) window.clearTimeout(activeShooterTimer.current)
        setActiveShooterCall({ name, text: call })
        activeShooterTimer.current = window.setTimeout(() => setActiveShooterCall(null), 3000)
      }

      stream.current = connectTableStream(tableId, (envelope) => {
        // DiceRolled itself is queued too (not applied early) — that
        // keeps tableState.dice/phase/point/puckOn changing in lockstep
        // with chips/fade-ups once flushed, instead of the puck jumping
        // before the dice have even shown a result.
        if (envelope.type === 'DiceRolled') {
          diceAnimating.current = true
          // Opens the instant this round starts, not later at settle —
          // that's what makes this race-free regardless of animation
          // speed or how fast the backend publishes the next round's
          // prep. See the awaitingReveal/inPrepPhase comment above.
          awaitingReveal.current = true
          inPrepPhase.current = false
          setAwaitingRoll(true)
          diceAnimationRef.current?.enqueue(envelope.dice)
        }
        // Marks the start of "next round's prep" — everything from
        // here until the next DiceRolled belongs to the upcoming roll,
        // not the one that just resolved (see table_session.py's
        // _drive(): prepare_next_roll() runs, unconditionally
        // publishing BetsRequested first, before the pause gate/pace
        // ever let roll_and_resolve() fire).
        if (envelope.type === 'BetsRequested') {
          inPrepPhase.current = true
        }
        // ShooterAssigned and PointHit both fire the roster speech
        // bubble immediately — never gated behind diceAnimating (it's
        // not tied to any roll's outcome-reveal timing) and never
        // suppressed at Turbo (rapid flicker there is expected, not a
        // bug). A fresh announcement replaces whatever bubble/timer was
        // already showing.
        if (envelope.type === 'ShooterAssigned') {
          currentShooterName.current = envelope.shooter_name
          showDealerCall(envelope.shooter_name)
        }
        if (envelope.type === 'PointHit' && currentShooterName.current) {
          showDealerCall(currentShooterName.current)
        }

        if (inPrepPhase.current) {
          // Next round's prep: held back until the current round's
          // animation *and* the extra reveal delay both finish (see
          // handleDiceSettled) — never merged into pendingEnvelopes,
          // which flushes right at settle with no extra delay.
          if (awaitingReveal.current) revealQueue.current.push(envelope)
          else applyAndUnlockRoll(envelope)
        } else if (diceAnimating.current) {
          pendingEnvelopes.current.push(envelope)
        } else {
          applyAndUnlockRoll(envelope)
        }
      })
    },
    [applyAndUnlockRoll],
  )

  // Applies exactly the OLDEST unflushed round's resolution envelopes
  // out of pendingEnvelopes — not everything currently queued.
  //
  // At the default pace (500ms between rolls) the backend routinely
  // outpaces the ~1000ms dice-settle animation: a second round's own
  // DiceRolled can arrive while the first round's dice are still
  // mid-flight. DiceAnimation queues and plays every such result in
  // full, one after another (dice/DiceAnimation.tsx's `queuedResult` —
  // it never drops one), so onSettled() still fires once per round,
  // just later than the backend produced it — but pendingEnvelopes can
  // already hold *two* rounds' worth of resolution data by the time
  // the first onSettled() call happens. Flushing all of it there used
  // to apply a later round's resolution before its own dice had
  // visually landed — and, worse, before that round's own BetPlaced
  // (held separately in revealQueue) had even been revealed yet,
  // orphaning its pop and leaving the *next* round's BetPlaced to
  // stack onto the same felt zone once revealQueue eventually caught
  // up (two $10 Pass Line placements merging into one $20 pile — a
  // real reported bug). Slicing at the next DiceRolled boundary here
  // keeps every round's resolution flushed only on its own onSettled().
  const flushOneRoundOfPending = useCallback(() => {
    const queue = pendingEnvelopes.current
    if (queue.length === 0) return
    const nextIdx = queue.findIndex((e, i) => i > 0 && e.type === 'DiceRolled')
    const thisRound = nextIdx === -1 ? queue : queue.slice(0, nextIdx)
    pendingEnvelopes.current = nextIdx === -1 ? [] : queue.slice(nextIdx)
    for (const envelope of thisRound) applyEnvelope(envelope)
  }, [applyEnvelope])

  // Applies exactly the OLDEST unflushed round's prep batch (BetsRequested
  // through RoundReady) out of revealQueue — the reveal-side counterpart
  // to flushOneRoundOfPending, for the same reason: multiple rounds' worth
  // of prep can queue up before the first one's reveal timer fires.
  // Leaves awaitingReveal open (and schedules nothing further itself) if
  // more batches are still waiting — the *next* one only reveals once its
  // own round's resolution has also been flushed (see startOrContinueReveal),
  // so a later round's bets never appear before an earlier round's dice
  // have actually resolved.
  const flushOneRoundOfReveal = useCallback(() => {
    const queue = revealQueue.current
    if (queue.length === 0) return
    const endIdx = queue.findIndex((e) => e.type === 'RoundReady')
    const thisRound = endIdx === -1 ? queue : queue.slice(0, endIdx + 1)
    revealQueue.current = endIdx === -1 ? [] : queue.slice(endIdx + 1)
    for (const envelope of thisRound) applyAndUnlockRoll(envelope)
    if (revealQueue.current.length === 0) awaitingReveal.current = false
  }, [applyAndUnlockRoll])

  // Called after each pendingEnvelopes flush: if there's a next round's
  // prep already waiting, count down the reveal beat for it (skipped at
  // Turbo). Deliberately does NOT chain into any *further* queued batch
  // itself — that only happens once the round in between has settled its
  // own dice too, via the next flushOneRoundOfPending → this call.
  const startOrContinueReveal = useCallback(() => {
    if (revealQueue.current.length === 0) return
    if (revealTimer.current) window.clearTimeout(revealTimer.current)
    if (speed >= MAX_SPEED) flushOneRoundOfReveal()
    else revealTimer.current = window.setTimeout(flushOneRoundOfReveal, REVEAL_DELAY_MS)
  }, [speed, flushOneRoundOfReveal])

  // DiceAnimation calls this once a roll's dice have landed.
  const handleDiceSettled = useCallback(() => {
    flushOneRoundOfPending()
    // Another round's DiceRolled+resolution is already queued behind
    // this one (DiceAnimation is about to chain straight into its own
    // animation) — stay "animating" so incoming envelopes keep queuing
    // correctly until *its* own onSettled() call handles them.
    if (pendingEnvelopes.current.length === 0) diceAnimating.current = false
    startOrContinueReveal()
  }, [flushOneRoundOfPending, startOrContinueReveal])

  // Creates the table and starts it landing paused — Start does not
  // set the game rolling, it just makes the rail's Play/Roll/Turbo
  // controls available. A separate start()-then-pause() used to do
  // this and lost the race almost every time: table_session.py's
  // drive loop only checks its pause gate once per iteration, *before*
  // the pacing sleep, so a pause() arriving during that sleep can
  // never cancel the roll already in flight — the first roll fired
  // regardless, ~500ms after Start. start_paused clears the gate
  // before the drive task is even scheduled, so it lands genuinely
  // paused with zero rolls.
  const handleStart = useCallback(async () => {
    try {
      setCreating(true)
      setError(null)
      const lineup = seats.filter((s) => s.enabled).map((s) => ({ name: s.name, strategy: s.name }))
      const created = await api.createTable({
        players: lineup,
        num_shooters: numShooters,
        roll_delay_ms: DEFAULT_ROLL_DELAY_MS,
      })
      attach(created.table_id)
      setPlayerName(created.players[0]?.name ?? '')
      setSpeed(1)
      setSnapshot(await api.start(created.table_id, true))
    } catch (e) {
      setError(String(e))
    } finally {
      setCreating(false)
    }
  }, [attach, numShooters, seats])

  // These three race against the SSE stream: `snapshot.state` in the
  // closure can be a beat stale by the time the request actually
  // lands (e.g. the table finishes server-side between a click and
  // the request completing), so the server can legitimately reject
  // with a 409 even though the button was enabled when clicked. The
  // stream's own next envelope will correct `snapshot` regardless —
  // these just need to not blow up as an unhandled rejection when it
  // happens, same as handleStart already does for its own errors.
  const handlePauseResume = useCallback(async () => {
    if (!snapshot) return
    try {
      setSnapshot(snapshot.state === 'paused' ? await api.resume(snapshot.table_id) : await api.pause(snapshot.table_id))
    } catch (e) {
      setError(String(e))
    }
  }, [snapshot])

  const handleSpeedChange = useCallback(
    async (next: number) => {
      setSpeed(next)
      if (!snapshot) return
      try {
        const rollDelayMs = next >= MAX_SPEED ? 0 : Math.round(DEFAULT_ROLL_DELAY_MS / next)
        setSnapshot(await api.setPace(snapshot.table_id, rollDelayMs))
      } catch (e) {
        setError(String(e))
      }
    },
    [snapshot],
  )

  const handleStep = useCallback(async () => {
    if (!snapshot) return
    // Optimistic: disables Roll the instant it's clicked, not only
    // once RoundReady eventually arrives for the *next* round — a
    // rejected request re-enables it below, same spirit as the other
    // handlers' error handling.
    setAwaitingRoll(true)
    try {
      setSnapshot(await api.step(snapshot.table_id))
    } catch (e) {
      setError(String(e))
      setAwaitingRoll(false)
    }
  }, [snapshot])

  // Tears down the current table (best-effort — it may already be
  // finished server-side) and drops the UI back to the lineup builder
  // for a fresh Start, without a page reload.
  const handleReset = useCallback(async () => {
    if (snapshot && snapshot.state !== 'finished' && snapshot.state !== 'stopped') {
      await api.stop(snapshot.table_id).catch(() => {})
    }
    stream.current?.close()
    setSnapshot(null)
    setState(initialState())
    setRollLog(initialRollLogState())
    setFeed(initialPlayByPlay())
    setPlayerName('')
    setSpeed(1)
    setError(null)
    diceAnimating.current = false
    pendingEnvelopes.current = []
    diceAnimationRef.current?.reset()
    awaitingReveal.current = false
    inPrepPhase.current = false
    revealQueue.current = []
    if (revealTimer.current) window.clearTimeout(revealTimer.current)
    revealTimer.current = null
    setAwaitingRoll(false)
    if (activeShooterTimer.current) window.clearTimeout(activeShooterTimer.current)
    activeShooterTimer.current = null
    setActiveShooterCall(null)
    currentShooterName.current = null
  }, [snapshot])

  const roster: RosterEntry[] = snapshot?.players.map((p) => ({ name: p.name, strategy: p.strategy })) ?? []
  const obsRoster: ObsPlayerRow[] =
    snapshot?.players.map((p, i) => {
      const live = state.players.get(p.name)
      return {
        name: p.name,
        strategy: p.strategy,
        color: PLAYER_COLORS[i % PLAYER_COLORS.length],
        bankroll: live?.bankroll ?? p.bankroll ?? 0,
        net: netFor(live),
        startingBankroll: live && live.history.length > 0 ? live.history[0] : null,
        history: live?.history ?? [],
      }
    }) ?? []
  const graphPlayers: GraphPlayer[] =
    snapshot?.players.map((p, i) => ({
      name: p.name,
      strategy: p.strategy,
      color: PLAYER_COLORS[i % PLAYER_COLORS.length],
      history: state.players.get(p.name)?.history ?? [],
      atRiskHistory: state.players.get(p.name)?.atRiskHistory ?? [],
    })) ?? []
  const sevenOutIndices = rollLog.rolls.reduce<number[]>((acc, r, i) => {
    if (r.type === 'seven-out') acc.push(i)
    return acc
  }, [])
  const rollTotals = rollLog.rolls.map((r) => r.total)

  return (
    <>
      <LiveFelt
        tableState={state}
        rollLog={rollLog}
        playerName={playerName}
        setPlayerName={setPlayerName}
        roster={roster}
        setTableState={setState}
        diceAnimationRef={diceAnimationRef}
        diceSpeed={speed}
        onDiceSettled={handleDiceSettled}
        sidebar={
          <ObservatoryPanel
            hasTable={snapshot !== null}
            seats={seats}
            onToggleSeat={handleToggleSeat}
            onSelectAll={handleSelectAll}
            onClearAll={handleClearAll}
            numShooters={numShooters}
            onNumShootersChange={setNumShooters}
            canStart={seats.some((s) => s.enabled)}
            creating={creating}
            error={error}
            onStart={handleStart}
            sessionState={snapshot?.state ?? null}
            awaitingRoll={awaitingRoll}
            onPauseResume={handlePauseResume}
            onStep={handleStep}
            onReset={handleReset}
            speed={speed}
            onSpeedChange={handleSpeedChange}
            roster={obsRoster}
            selectedPlayer={playerName}
            onSelectPlayer={setPlayerName}
            feed={feed}
            rolls={rollTotals}
            dice={state.dice}
            activeShooterCall={activeShooterCall}
          />
        }
      />
      <SessionGraph players={graphPlayers} totalRolls={rollLog.rolls.length} sevenOutIndices={sevenOutIndices} />
    </>
  )
}
