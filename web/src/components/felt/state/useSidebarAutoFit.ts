import { useEffect, useRef, useState } from 'react'

/**
 * The scale-to-fit arithmetic, isolated as a pure function so it can
 * be unit-tested with plain numbers — no DOM, no jsdom. Only ever
 * shrinks (never magnifies past 1:1): collapsing sections routinely
 * leaves the natural content far shorter than the available height,
 * and an earlier version that let this grow past 1 blew the sidebar's
 * text out past its own fixed width once enough sections were
 * collapsed (see the prototype's own comment on syncSidebarHeight —
 * a documented past bug, not a hypothetical one).
 */
export function computeSidebarScale(availH: number, naturalH: number): number {
  if (naturalH <= 0) return 1
  return Math.min(1, availH / naturalH)
}

/**
 * Sizes the sidebar box to match the felt's rendered height, then
 * scales its inner content down (never up) to avoid a scrollbar when
 * it would overflow. Two ResizeObservers do the work a manual
 * syncSidebarHeight()-after-every-toggle call did in the prototype:
 * one on the felt SVG (the target height to match), one on the inner
 * content wrapper itself (so a section collapsing/expanding — which
 * changes layout size via display:none, not just a CSS transform —
 * triggers a re-fit with no prop-drilled callback needed). A CSS
 * `transform: scale()` doesn't affect the observed border-box size,
 * so this can't feed back into itself.
 */
export function useSidebarAutoFit() {
  const sidebarRef = useRef<HTMLDivElement>(null)
  const innerRef = useRef<HTMLDivElement>(null)
  const [height, setHeight] = useState<number>()
  const [scale, setScale] = useState(1)

  useEffect(() => {
    const felt = document.getElementById('felt')
    const sidebar = sidebarRef.current
    const inner = innerRef.current
    if (!felt || !sidebar || !inner) return

    const sync = () => {
      setHeight(felt.getBoundingClientRect().height)
      inner.style.transform = 'scale(1)'
      const availH = sidebar.clientHeight - 14 // minus 7px top/bottom padding
      const naturalH = inner.scrollHeight
      setScale(computeSidebarScale(availH, naturalH))
    }

    sync()
    const feltObserver = new ResizeObserver(sync)
    feltObserver.observe(felt)
    const innerObserver = new ResizeObserver(sync)
    innerObserver.observe(inner)
    window.addEventListener('resize', sync)
    return () => {
      feltObserver.disconnect()
      innerObserver.disconnect()
      window.removeEventListener('resize', sync)
    }
  }, [])

  return { sidebarRef, innerRef, height, scale }
}
