import { render, screen } from '@testing-library/react'
import { SearchMeta } from './SearchMeta'

describe('SearchMeta', () => {
  it('renders searched and returned portal counts', () => {
    render(<SearchMeta portalsSearched={2} portalsReturned={2} />)

    expect(screen.getByText('Searched 2 portals · 2 results')).toBeInTheDocument()
    expect(screen.queryByText(/dropped/i)).not.toBeInTheDocument()
  })

  it('renders dropped count if present', () => {
    render(
      <SearchMeta
        portalsSearched={3}
        portalsReturned={2}
        portalsDropped={['https://magicbricks.com/dropped']}
      />,
    )

    expect(screen.getByText('Searched 3 portals · 2 results')).toBeInTheDocument()
    expect(screen.getByText('(1 empty or invalid results dropped)')).toBeInTheDocument()
  })

  it('renders default applied notes mapped to human friendly text', () => {
    render(
      <SearchMeta
        portalsSearched={2}
        portalsReturned={2}
        defaultsApplied={['radius_km: 4', 'budget_min: 0']}
      />,
    )

    expect(screen.getByText('4 km radius search applied')).toBeInTheDocument()
    expect(screen.getByText('Budget floor assumed as ₹0')).toBeInTheDocument()
  })
})
