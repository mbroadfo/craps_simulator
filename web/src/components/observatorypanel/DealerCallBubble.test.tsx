// @vitest-environment jsdom
import '@testing-library/jest-dom/vitest'
import { cleanup, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'
import { DealerCallBubble } from './DealerCallBubble'

afterEach(() => {
  cleanup()
})

describe('DealerCallBubble', () => {
  it('renders the given text', () => {
    render(<DealerCallBubble text="$10 on the line" />)
    expect(screen.getByText('$10 on the line')).toBeInTheDocument()
  })

  // No visible=false case — the component has no such prop. Whether
  // it shows at all is entirely the caller's decision (BotRoster only
  // renders it for the row matching the active shooter); see the
  // component's own header comment for why timing/visibility live in
  // App.tsx rather than here.
})
