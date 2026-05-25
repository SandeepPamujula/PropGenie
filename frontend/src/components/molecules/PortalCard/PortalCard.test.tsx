import { render, screen } from '@testing-library/react'
import type { PortalResult } from '../../../types/domain'
import { PortalCard } from './PortalCard'

describe('PortalCard', () => {
  const mockCardRent: PortalResult = {
    portal: 'nobroker',
    label: '3 BHK in HSR Layout',
    summary: '3BHK rentals near HSR Layout, Bangalore — ₹30K to ₹40K/mo',
    url: 'https://nobroker.in/test-rent',
    isPriority: true,
    notes: '4 km radius search applied',
  }

  const mockCardBuy: PortalResult = {
    portal: '99acres',
    label: '2 BHK Villa in Whitefield',
    summary: '2BHK villas for sale in Whitefield, Bangalore — ₹1.2Cr to ₹1.5Cr',
    url: 'https://99acres.com/test-buy',
    isPriority: true,
    notes: 'Budget floor assumed as ₹0',
  }

  it('renders NoBroker rent card with priority badge', () => {
    render(<PortalCard card={mockCardRent} />)

    // Check portal badge display
    expect(screen.getByText('NoBroker')).toBeInTheDocument()

    // Check priority badge for rent
    expect(screen.getByText('Best for Rent')).toBeInTheDocument()

    // Check details
    expect(screen.getByText('3 BHK in HSR Layout')).toBeInTheDocument()
    expect(screen.getByText('3BHK rentals near HSR Layout, Bangalore — ₹30K to ₹40K/mo')).toBeInTheDocument()
    expect(screen.getByText('4 km radius search applied')).toBeInTheDocument()

    // Check CTA link
    const ctaLink = screen.getByRole('link', { name: /View on NoBroker/i })
    expect(ctaLink).toBeInTheDocument()
    expect(ctaLink).toHaveAttribute('href', 'https://nobroker.in/test-rent')
    expect(ctaLink).toHaveAttribute('target', '_blank')
    expect(ctaLink).toHaveAttribute('rel', 'noopener noreferrer')
  })

  it('renders 99acres buy card with priority badge', () => {
    render(<PortalCard card={mockCardBuy} />)

    // Check portal badge display
    expect(screen.getByText('99acres')).toBeInTheDocument()

    // Check priority badge for buy
    expect(screen.getByText('Best for Buy')).toBeInTheDocument()

    // Check details
    expect(screen.getByText('2 BHK Villa in Whitefield')).toBeInTheDocument()
    expect(screen.getByText('2BHK villas for sale in Whitefield, Bangalore — ₹1.2Cr to ₹1.5Cr')).toBeInTheDocument()
    expect(screen.getByText('Budget floor assumed as ₹0')).toBeInTheDocument()

    // Check CTA link
    const ctaLink = screen.getByRole('link', { name: /View on 99acres/i })
    expect(ctaLink).toBeInTheDocument()
    expect(ctaLink).toHaveAttribute('href', 'https://99acres.com/test-buy')
    expect(ctaLink).toHaveAttribute('target', '_blank')
    expect(ctaLink).toHaveAttribute('rel', 'noopener noreferrer')
  })

  it('renders non-priority cards without priority badge', () => {
    const nonPriorityCard: PortalResult = {
      ...mockCardRent,
      portal: 'magicbricks',
      isPriority: false,
    }

    render(<PortalCard card={nonPriorityCard} />)

    expect(screen.getByText('MagicBricks')).toBeInTheDocument()
    expect(screen.queryByText('Best for Rent')).not.toBeInTheDocument()
    expect(screen.queryByText('Priority Choice')).not.toBeInTheDocument()
  })
})
