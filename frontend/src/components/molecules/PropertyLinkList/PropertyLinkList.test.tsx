import { render, screen } from '@testing-library/react'
import { PropertyLinkList } from './PropertyLinkList'

describe('PropertyLinkList', () => {
  const mockLinks = [
    {
      url: 'https://nobroker.in/prop-1',
      portal: 'NoBroker',
      rank: 1,
      validation: { schema_valid: true, head_status: 200 },
    },
    {
      url: 'https://nobroker.in/prop-2',
      portal: 'NoBroker',
      rank: 2,
      validation: { schema_valid: true, head_status: 200 },
    },
    {
      url: 'https://nobroker.in/prop-3',
      portal: 'NoBroker',
      rank: 3,
      validation: { schema_valid: true, head_status: 200 },
    },
    {
      url: 'https://nobroker.in/prop-4',
      portal: 'NoBroker',
      rank: 4,
      validation: { schema_valid: true, head_status: 200 },
    },
    {
      url: 'https://nobroker.in/prop-5',
      portal: 'NoBroker',
      rank: 5,
      validation: { schema_valid: true, head_status: 200 },
    },
    {
      url: 'https://nobroker.in/prop-6',
      portal: 'NoBroker',
      rank: 6,
      validation: { schema_valid: true, head_status: 200 },
    },
  ]

  it('renders null when propertyLinks is undefined or empty', () => {
    const { container } = render(
      <PropertyLinkList
        propertyLinks={[]}
        portalDisplayName="NoBroker"
        portalNameLower="nobroker"
      />
    )
    expect(container.firstChild).toBeNull()

    const { container: containerUndefined } = render(
      <PropertyLinkList
        portalDisplayName="NoBroker"
        portalNameLower="nobroker"
      />
    )
    expect(containerUndefined.firstChild).toBeNull()
  })

  it('renders loading shimmer state when isLoading is true', () => {
    const { container } = render(
      <PropertyLinkList
        propertyLinks={[]}
        portalDisplayName="NoBroker"
        portalNameLower="nobroker"
        isLoading={true}
      />
    )
    expect(container.querySelector('#property-links-loading-nobroker')).toBeInTheDocument()
    expect(screen.queryByText('Top Listings Found')).not.toBeInTheDocument()
  })

  it('renders list of links up to max 5 links', () => {
    render(
      <PropertyLinkList
        propertyLinks={mockLinks}
        portalDisplayName="NoBroker"
        portalNameLower="nobroker"
      />
    )

    // Check header
    expect(screen.getByText('Top Listings Found')).toBeInTheDocument()

    // Check 5 links are rendered
    expect(screen.getByText('View Property #1 on NoBroker')).toBeInTheDocument()
    expect(screen.getByText('View Property #2 on NoBroker')).toBeInTheDocument()
    expect(screen.getByText('View Property #3 on NoBroker')).toBeInTheDocument()
    expect(screen.getByText('View Property #4 on NoBroker')).toBeInTheDocument()
    expect(screen.getByText('View Property #5 on NoBroker')).toBeInTheDocument()

    // Link 6 should NOT be rendered (capped at 5)
    expect(screen.queryByText('View Property #6 on NoBroker')).not.toBeInTheDocument()

    // Check attributes of a rendered link
    const link1 = screen.getByRole('link', { name: /View Property #1 on NoBroker/i })
    expect(link1).toHaveAttribute('href', 'https://nobroker.in/prop-1')
    expect(link1).toHaveAttribute('target', '_blank')
    expect(link1).toHaveAttribute('rel', 'noopener noreferrer')
  })
})
