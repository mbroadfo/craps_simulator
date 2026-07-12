import { useEffect, useState } from 'react'
import { FELT_W } from '../layout'

/**
 * The felt SVG scales fluidly with .tableWrap's CSS width (via
 * viewBox), but plain HTML siblings outside the SVG — the denom
 * picker, and later the Roll/Clear buttons — don't get that for free;
 * fixed-px CSS sizes stay a constant screen size regardless of how big
 * the table renders. This measures the felt's actual rendered width
 * via ResizeObserver and returns renderedWidth / FELT_W (1400, the
 * viewBox width) so those HTML pieces can size themselves off it —
 * `size * scale` instead of a bare literal. Not a prototype behavior
 * (the prototype has this same fixed-px mismatch) — a deliberate
 * improvement made during the port, at Mike's request.
 */
export function useFeltScale(feltId = 'felt'): number {
  const [scale, setScale] = useState(1)

  useEffect(() => {
    const el = document.getElementById(feltId)
    if (!el) return
    const update = () => setScale(el.getBoundingClientRect().width / FELT_W)
    update()
    const ro = new ResizeObserver(update)
    ro.observe(el)
    return () => ro.disconnect()
  }, [feltId])

  return scale
}
