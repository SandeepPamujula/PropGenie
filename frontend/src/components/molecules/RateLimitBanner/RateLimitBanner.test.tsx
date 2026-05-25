import { render, screen } from '@testing-library/react'
import { RateLimitBanner, getISTResetTimeString } from './RateLimitBanner'

describe('RateLimitBanner', () => {
  it('renders the rate limit banner message and reset time correctly with default props', () => {
    render(<RateLimitBanner />)

    const banner = document.querySelector('#rate-limit-banner')
    expect(banner).toBeInTheDocument()

    const text = screen.getByText(/You've reached your daily search limit of 10/i)
    expect(text).toBeInTheDocument()
    expect(text.id).toBe('rate-limit-banner-text')

    const resetTime = screen.getByText(/Next reset: 12:00 AM IST on/i)
    expect(resetTime).toBeInTheDocument()
    expect(resetTime.id).toBe('rate-limit-banner-reset-time')
  })

  it('renders custom maxSearches limit correctly', () => {
    render(<RateLimitBanner maxSearches={5} />)

    expect(
      screen.getByText(/You've reached your daily search limit of 5. Please try again tomorrow!/i),
    ).toBeInTheDocument()
  })

  it('renders custom resetTimeIST correctly', () => {
    const customTime = '12:00 AM IST on 2026-06-01'
    render(<RateLimitBanner resetTimeIST={customTime} />)

    expect(screen.getByText(`Next reset: ${customTime}`)).toBeInTheDocument()
  })

  it('correctly calculates the next midnight in IST', () => {
    const timeStr = getISTResetTimeString()
    expect(timeStr).toMatch(/^12:00 AM IST on \d{4}-\d{2}-\d{2}$/)
  })
})
