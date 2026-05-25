import { render, screen } from '@testing-library/react'
import type { PortalResult } from '../../../types/domain'
import { PortalCardList } from './PortalCardList'

describe('PortalCardList', () => {
  const mockCards: PortalResult[] = [
    {
      portal: 'magicbricks',
      label: 'MB Card',
      summary: 'MB Rent summary',
      url: 'https://magicbricks.com',
      isPriority: false,
    },
    {
      portal: 'nobroker',
      label: 'NB Card',
      summary: 'NB Rent summary',
      url: 'https://nobroker.in',
      isPriority: true,
    },
  ]

  it('renders cards sorted with priority card first', () => {
    const { container } = render(<PortalCardList cards={mockCards} />)

    // Check that both cards are rendered
    expect(screen.getByText('NoBroker')).toBeInTheDocument()
    expect(screen.getByText('MagicBricks')).toBeInTheDocument()

    // Verify ordering by checking id order in DOM
    const cardElements = container.querySelectorAll('.glass-card')
    expect(cardElements).toHaveLength(2)
    expect(cardElements[0]).toHaveAttribute('id', 'portal-card-nobroker')
    expect(cardElements[1]).toHaveAttribute('id', 'portal-card-magicbricks')
  })
})
