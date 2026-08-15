/**
 * Two animated dice overlaying the felt SVG — a real WebGL scene
 * (Three.js), not CSS transforms. Phase A tried a CSS 3D cube; two
 * rounds of tuning couldn't get past CSS 3D's structural limits (no
 * real camera/lens, no real lighting, visible seams between faces).
 * Phase B replaced the renderer with Three.js + a live Cannon-es
 * rigid-body simulation for the flight — closer to "real" physics,
 * but a live simulation can only ever be *aimed* at a landing spot,
 * and collision-solver instability twice sent dice flying off the
 * felt or pinned against its edges in ways no amount of gravity/
 * restitution tuning fully fixed. This version drops the physics
 * engine: POSITION and ROTATION are both deterministic functions of
 * elapsed time, built backward from the already-known landing point
 * and rolled result — see diceLayout.ts's archPoint/bounceOffset for
 * position and this file's tumbleQuaternion for rotation. Where a die
 * lands IS where it tumbles to, because the formulas' own t=1 value
 * is that exact landing spot/face — not a physics simulation that's
 * merely hoped to arrive there.
 *
 * The felt SVG itself is never touched: this renders as an
 * absolutely-positioned sibling of `<svg id="felt">` inside
 * `.tableWrap` (see Felt.tsx), z-index 10.
 *
 * jsdom has no WebGL, so scene setup is wrapped in try/catch — if it
 * fails (headless test environment, or a real browser with WebGL
 * disabled), the component still runs its phase timers and calls
 * `onSettled` on schedule, just without anything visible. This keeps
 * the gating contract App.tsx depends on decoupled from whether
 * rendering actually works.
 *
 * App.tsx holds back chip/fade-up/ATS-affecting state updates until
 * `onSettled` fires — see its own comment for why that gating lives
 * there instead of here.
 *
 * Rolls are pushed in via an imperative `enqueue()` (a ref handle),
 * not a `result` prop. That's deliberate, not a style choice: React
 * batches state updates, and for a plain (non-functional) `setState`
 * call, only the *last* value in a batch survives — at Turbo/fast
 * pace the backend can publish many DiceRolled events within a single
 * JS tick, all arriving before React ever renders. A `result` prop
 * fed via `setDiceResult(...)` used to silently collapse a whole
 * burst of rolls down to just the final one, so DiceAnimation (and
 * the one onSettled() call per roll App.tsx's queue-draining depends
 * on) never even saw most of them — everything from that point stayed
 * stuck in App.tsx's pending queues for the rest of the session (a
 * real reported bug: the felt looked like it had stopped, well before
 * all shooters had actually played out server-side). `enqueue()` runs
 * synchronously in the SSE handler itself, outside React state
 * entirely, so every roll reliably reaches the queue below exactly
 * once — same reasoning as `queuedResults` itself (a real FIFO, not a
 * single overwritable slot) one level up.
 */
import { forwardRef, useEffect, useImperativeHandle, useRef, useState } from 'react'
import * as THREE from 'three'
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js'
import './DiceAnimation.css'
import {
  archPoint,
  bounceOffset,
  computeDieWaypoints,
  FELT_VIEWBOX_H,
  FELT_VIEWBOX_W,
  pickLandingCenter,
  pipsForFace,
  settleRotationForValue,
  toWorldPosition,
  type DieWaypoints,
  type GroundPoint,
} from './diceLayout'

type Phase = 'idle' | 'launching' | 'bouncing' | 'settled'

const FLIGHT_MS = 700
const BOUNCE_MS = 300
const FAST_FLIGHT_MS = 300 // speed >= 5x: shortened, no bounce
const ROLL_SOUND_URL = '/sounds/dice-roll.mp3'

const DIE_HALF = 35 // world units (== felt viewBox units)
const RESTING_Y = DIE_HALF
const ARCH_PEAK = 140 // height above resting at the arc's midpoint
const BOUNCE_HEIGHT = 20 // decorative post-landing settle bounce
const BOUNCE_CYCLES = 2.5

// Which cube axis holds which value — opposite faces sum to 7, like a
// real die. Order here must match Three.js's BoxGeometry material
// slots: [+X, -X, +Y, -Y, +Z, -Z].
const FACE_VALUES = [2, 5, 1, 6, 3, 4]

function durationsFor(speed: number) {
  if (speed >= 10) return { flightMs: 0, bounceMs: 0 } // Turbo: skip the animation entirely
  if (speed >= 5) return { flightMs: FAST_FLIGHT_MS, bounceMs: 0 }
  return { flightMs: FLIGHT_MS, bounceMs: BOUNCE_MS }
}

function createFaceTexture(value: number): THREE.CanvasTexture {
  const canvas = document.createElement('canvas')
  canvas.width = 128
  canvas.height = 128
  const ctx = canvas.getContext('2d')
  if (ctx) {
    ctx.fillStyle = '#f5f5f0'
    ctx.fillRect(0, 0, 128, 128)
    ctx.strokeStyle = '#e0ddd8'
    ctx.lineWidth = 4
    ctx.strokeRect(2, 2, 124, 124)
    ctx.fillStyle = '#111111'
    const scale = 128 / 48
    for (const p of pipsForFace(value)) {
      ctx.beginPath()
      ctx.arc(p.x * scale, p.y * scale, p.r * scale, 0, Math.PI * 2)
      ctx.fill()
    }
  }
  const texture = new THREE.CanvasTexture(canvas)
  texture.colorSpace = THREE.SRGBColorSpace
  return texture
}

function targetQuaternion(value: number): THREE.Quaternion {
  const rot = settleRotationForValue(value)
  const euler = new THREE.Euler(
    THREE.MathUtils.degToRad(rot.x),
    THREE.MathUtils.degToRad(rot.y),
    THREE.MathUtils.degToRad(rot.z),
  )
  return new THREE.Quaternion().setFromEuler(euler)
}

// Fixed (not random) per-die spin axes — the two dice tumble around
// visibly different axes so they never look identical mid-flight, but
// which axis is a deterministic constant, not chosen per roll.
const SPIN_AXES: [THREE.Vector3, THREE.Vector3] = [
  new THREE.Vector3(1, 1, 0.4).normalize(),
  new THREE.Vector3(-1, 1, -0.4).normalize(),
]
const TOTAL_TURNS = 3 // extra full rotations before landing exactly on the target face

// A second, smaller spin around a *different* fixed axis, composed on
// top of the primary one. A single-axis spin reads as a spinning coin
// — real tumbling dice constantly change their apparent rotation axis
// (precession/wobble), which is what actually reads as "tumbling"
// rather than "spinning." Using a different decay power (squared, not
// cubed) than the primary term means the two decelerate at slightly
// different rates instead of staying in lockstep, which is what
// breaks up the otherwise-too-clean single-spin look.
const WOBBLE_AXES: [THREE.Vector3, THREE.Vector3] = [
  new THREE.Vector3(0.2, -1, 0.9).normalize(),
  new THREE.Vector3(0.2, 1, -0.9).normalize(),
]
const WOBBLE_TURNS = 1.25

/**
 * The die's displayed orientation at fraction `t` (0=launch, 1=landed)
 * of the flight: a primary spin (`TOTAL_TURNS`) plus a smaller wobble
 * spin around a different axis (`WOBBLE_TURNS`), both decelerating
 * down to exactly zero *at* t=1 — a 360°-multiple rotation is
 * visually the identity, so both terms vanish there and this is
 * exactly `target`, no snap needed. At t=0 it's also visually
 * `target` (whole multiples of turns away on both axes) — invisible
 * in practice since the die is spinning at its fastest right there,
 * same principle a prize-wheel "spin then land on X" animation uses.
 */
function tumbleQuaternion(target: THREE.Quaternion, axis: THREE.Vector3, wobbleAxis: THREE.Vector3, t: number): THREE.Quaternion {
  const clamped = Math.min(Math.max(t, 0), 1)
  const spin = new THREE.Quaternion().setFromAxisAngle(axis, TOTAL_TURNS * Math.PI * 2 * Math.pow(1 - clamped, 3))
  const wobble = new THREE.Quaternion().setFromAxisAngle(wobbleAxis, WOBBLE_TURNS * Math.PI * 2 * Math.pow(1 - clamped, 2))
  return spin.multiply(wobble).multiply(target)
}

interface DieRig {
  mesh: THREE.Mesh
}

/**
 * Owns every Three.js object for the lifetime of the component —
 * created once on mount, reused across rolls (dice persist between
 * rolls, just repositioned/relaunched), disposed on unmount. Kept out
 * of React state entirely: nothing here should trigger a re-render,
 * it's driven by its own requestAnimationFrame loop.
 */
class DiceScene {
  private renderer: THREE.WebGLRenderer
  private scene = new THREE.Scene()
  private camera: THREE.OrthographicCamera
  private rigs: [DieRig, DieRig]
  private rafId: number | null = null
  private stopAt = 0

  constructor(canvas: HTMLCanvasElement) {
    this.renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true })
    this.renderer.setClearColor(0x000000, 0)
    this.renderer.shadowMap.enabled = true

    const halfW = FELT_VIEWBOX_W / 2
    const halfH = FELT_VIEWBOX_H / 2
    this.camera = new THREE.OrthographicCamera(-halfW, halfW, halfH, -halfH, 1, 2000)
    this.camera.position.set(halfW, 1000, halfH)
    this.camera.rotation.set(-Math.PI / 2, 0, 0)

    this.scene.add(new THREE.AmbientLight(0xffffff, 0.6))
    const sun = new THREE.DirectionalLight(0xffffff, 1.4)
    sun.position.set(halfW - 300, 900, halfH - 250)
    sun.target.position.set(halfW, 0, halfH)
    sun.castShadow = true
    sun.shadow.mapSize.set(1024, 1024)
    sun.shadow.camera.left = -halfW
    sun.shadow.camera.right = halfW
    sun.shadow.camera.top = halfH
    sun.shadow.camera.bottom = -halfH
    sun.shadow.camera.near = 1
    sun.shadow.camera.far = 2000
    this.scene.add(sun, sun.target)

    const shadowPlane = new THREE.Mesh(
      new THREE.PlaneGeometry(FELT_VIEWBOX_W * 2, FELT_VIEWBOX_H * 2),
      new THREE.ShadowMaterial({ opacity: 0.35 }),
    )
    shadowPlane.rotation.x = -Math.PI / 2
    shadowPlane.position.set(halfW, 0, halfH)
    shadowPlane.receiveShadow = true
    this.scene.add(shadowPlane)

    this.rigs = [this.buildRig(), this.buildRig()]
    this.render()
  }

  private buildRig(): DieRig {
    // A real die has chamfered edges/corners, not knife-sharp ones —
    // a plain BoxGeometry reads as flat/low-fi (each face a hard
    // rectangle with no highlight along the edge) no matter how good
    // the lighting is. RoundedBoxGeometry bevels the corners while
    // keeping BoxGeometry's own 6-face material grouping, so the
    // FACE_VALUES/materials mapping below is unaffected.
    const geometry = new RoundedBoxGeometry(DIE_HALF * 2, DIE_HALF * 2, DIE_HALF * 2, 4, 8)
    const materials = FACE_VALUES.map((v) => new THREE.MeshStandardMaterial({ map: createFaceTexture(v) }))
    const mesh = new THREE.Mesh(geometry, materials)
    mesh.castShadow = true
    mesh.visible = false
    this.scene.add(mesh)
    return { mesh }
  }

  resize(width: number, height: number) {
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2))
    this.renderer.setSize(width, height, false)
    this.render()
  }

  /**
   * Animates both dice from `waypoints`' launch point to their own
   * landing point, arriving exactly on the real rolled `result` at
   * t=1 of the flight — by construction, not by aiming a simulation
   * and hoping. POSITION follows archPoint (a simple parabola: linear
   * x/z, height peaking at the midpoint); ROTATION follows
   * tumbleQuaternion (a fixed number of extra spins decelerating to
   * exactly the target face). Both are pure functions of elapsed
   * time, so the same result/speed always produces the same-shaped
   * roll. The remaining time after the flight (`totalMs - flightMs`)
   * plays a small decorative settle bounce (bounceOffset) on top of
   * the already-landed x/z position — never enough to move the die
   * off its landing spot, just a vertical wobble.
   */
  startRoll(waypoints: [DieWaypoints, DieWaypoints], result: [number, number], flightMs: number, totalMs: number) {
    if (this.rafId !== null) cancelAnimationFrame(this.rafId)
    const targets: [THREE.Quaternion, THREE.Quaternion] = [targetQuaternion(result[0]), targetQuaternion(result[1])]
    const froms: [GroundPoint, GroundPoint] = [toWorldPosition(waypoints[0].launch), toWorldPosition(waypoints[1].launch)]
    const tos: [GroundPoint, GroundPoint] = [toWorldPosition(waypoints[0].landing), toWorldPosition(waypoints[1].landing)]

    for (let i = 0; i < 2; i++) {
      const { mesh } = this.rigs[i]
      mesh.visible = true
      const p = archPoint(froms[i], tos[i], 0, ARCH_PEAK)
      mesh.position.set(p.x, RESTING_Y + p.y, p.z)
      mesh.quaternion.copy(tumbleQuaternion(targets[i], SPIN_AXES[i], WOBBLE_AXES[i], 0))
    }

    const startedAt = performance.now()
    this.stopAt = startedAt + totalMs
    const bounceDuration = totalMs - flightMs
    const step = (now: number) => {
      const elapsed = now - startedAt
      const t = flightMs > 0 ? elapsed / flightMs : 1
      const bounceU = bounceDuration > 0 ? (elapsed - flightMs) / bounceDuration : 0
      for (let i = 0; i < 2; i++) {
        const { mesh } = this.rigs[i]
        const p = archPoint(froms[i], tos[i], t, ARCH_PEAK)
        const bounce = bounceOffset(bounceU, BOUNCE_HEIGHT, BOUNCE_CYCLES)
        mesh.position.set(p.x, RESTING_Y + p.y + bounce, p.z)
        mesh.quaternion.copy(tumbleQuaternion(targets[i], SPIN_AXES[i], WOBBLE_AXES[i], t))
      }
      this.render()
      if (now < this.stopAt) {
        this.rafId = requestAnimationFrame(step)
      } else {
        this.rafId = null
      }
    }
    this.rafId = requestAnimationFrame(step)
  }

  /** Stops the scripted motion and forces both dice to the real rolled result, at rest on their landing spots — the exact same values startRoll's own formulas already converge to at t=1, reasserted directly as a final source of truth (also what Turbo/instant settle uses, which never calls startRoll at all). */
  settle(waypoints: [DieWaypoints, DieWaypoints], result: [number, number]) {
    if (this.rafId !== null) {
      cancelAnimationFrame(this.rafId)
      this.rafId = null
    }
    waypoints.forEach((wp, i) => {
      const { mesh } = this.rigs[i]
      const at = toWorldPosition(wp.landing)
      mesh.visible = true
      mesh.position.set(at.x, RESTING_Y, at.z)
      mesh.quaternion.copy(targetQuaternion(result[i]))
    })
    this.render()
  }

  private render() {
    this.renderer.render(this.scene, this.camera)
  }

  dispose() {
    if (this.rafId !== null) cancelAnimationFrame(this.rafId)
    for (const { mesh } of this.rigs) {
      mesh.geometry.dispose()
      for (const m of mesh.material as THREE.MeshStandardMaterial[]) {
        m.map?.dispose()
        m.dispose()
      }
    }
    this.renderer.dispose()
  }
}

export interface DiceAnimationHandle {
  /** Push one roll's result in. Runs synchronously (see the module
   * docstring for why this is imperative, not a `result` prop). */
  enqueue: (result: [number, number]) => void
  /** Drops any in-flight/queued cycle and returns to idle — the
   * component itself persists across sessions (no remount), so a
   * fresh session's App.tsx reset must clear this too, or a stale
   * mid-animation cycle from the *previous* session could make the
   * new session's first enqueue() queue behind it instead of starting. */
  reset: () => void
}

export const DiceAnimation = forwardRef<DiceAnimationHandle, { speed: number; onSettled: () => void }>(
  function DiceAnimation({ speed, onSettled }, ref) {
    const [phase, setPhase] = useState<Phase>('idle')
    const canvasRef = useRef<HTMLCanvasElement>(null)
    const sceneRef = useRef<DiceScene | null>(null)
    const waypoints = useRef<[DieWaypoints, DieWaypoints] | null>(null)
    // A real FIFO, not a single slot: at normal speeds the backend can
    // outpace the ~1s animation by more than one roll (App.tsx's
    // per-round envelope draining now depends on onSettled() firing
    // exactly once per actual roll — see its own comment). A single
    // slot here used to let a third overlapping result silently
    // overwrite a second one that had never gotten its own settle yet,
    // permanently losing an onSettled() call and starving App.tsx's
    // queues, which never fully drain again for the rest of the session.
    const queuedResults = useRef<[number, number][]>([])
    // Authoritative "is a cycle currently running" flag for enqueue()'s
    // decision — a ref, deliberately not derived from the `phase` React
    // state. enqueue() can be called several times synchronously in a
    // row (a burst of SSE messages) with no render in between; reading
    // `phase` state there would see the same stale value on every call
    // in that burst, since state only updates on the next render — a
    // ref reflects the true current value the instant runCycle sets it.
    const cycleActive = useRef(false)
    const timers = useRef<number[]>([])

    useEffect(() => {
      const canvas = canvasRef.current
      if (!canvas) return
      try {
        sceneRef.current = new DiceScene(canvas)
      } catch {
        sceneRef.current = null // WebGL unavailable — phase timers/onSettled still run, just nothing renders
      }
      return () => {
        sceneRef.current?.dispose()
        sceneRef.current = null
      }
    }, [])

    // Same getBoundingClientRect()+ResizeObserver pattern useSidebarAutoFit.ts
    // uses for the same "responsive SVG, sibling canvas needs real pixels"
    // problem — the orthographic camera's frustum is fixed to the felt's
    // viewBox extents, so only the renderer's pixel size needs to track it.
    useEffect(() => {
      const felt = document.getElementById('felt')
      if (!felt) return
      const sync = () => {
        const box = felt.getBoundingClientRect()
        if (box.width > 0 && box.height > 0) sceneRef.current?.resize(box.width, box.height)
      }
      sync()
      const observer = new ResizeObserver(sync)
      observer.observe(felt)
      window.addEventListener('resize', sync)
      return () => {
        observer.disconnect()
        window.removeEventListener('resize', sync)
      }
    }, [])

    useEffect(() => {
      const clearTimers = () => {
        for (const id of timers.current) window.clearTimeout(id)
        timers.current = []
      }
      return clearTimers
    }, [])

    // No deps array: recreated every render so `runCycle` always closes
    // over the current `speed` prop — this component re-renders rarely
    // (only on real prop/state changes), so there's no meaningful cost
    // to skipping memoization here.
    useImperativeHandle(ref, () => ({
      enqueue(result: [number, number]) {
        if (cycleActive.current) {
          queuedResults.current.push(result)
          return
        }
        runCycle(result)
      },
      reset() {
        for (const id of timers.current) window.clearTimeout(id)
        timers.current = []
        queuedResults.current = []
        cycleActive.current = false
        setPhase('idle')
      },
    }))

    function runCycle(nextResult: [number, number]) {
      cycleActive.current = true
      for (const id of timers.current) window.clearTimeout(id)
      timers.current = []

      const { flightMs, bounceMs } = durationsFor(speed)
      const wp = computeDieWaypoints(pickLandingCenter())
      waypoints.current = wp

      if (flightMs > 0) {
        new Audio(ROLL_SOUND_URL).play().catch(() => {}) // autoplay can be blocked; a failed play() is silent, not an error
        sceneRef.current?.startRoll(wp, nextResult, flightMs, flightMs + bounceMs)
      }

      const settle = () => {
        sceneRef.current?.settle(wp, nextResult)
        setPhase('settled')
        onSettled()
        const next = queuedResults.current.shift()
        if (next) runCycle(next)
        else cycleActive.current = false
      }

      setPhase('launching')
      if (flightMs === 0) {
        settle()
        return
      }
      timers.current.push(
        window.setTimeout(() => {
          if (bounceMs > 0) {
            setPhase('bouncing')
            timers.current.push(window.setTimeout(settle, bounceMs))
          } else {
            settle()
          }
        }, flightMs),
      )
    }

    return (
      <div className="diceAnimation" data-phase={phase}>
        <canvas ref={canvasRef} />
      </div>
    )
  },
)
