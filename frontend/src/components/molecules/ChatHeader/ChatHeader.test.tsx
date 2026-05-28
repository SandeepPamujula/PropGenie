import { render, screen } from '@testing-library/react'
import { ChatHeader } from './ChatHeader'

describe('ChatHeader', () => {
  it('renders title, tagline, logo and search count correctly', () => {
    render(<ChatHeader currentSearches={4} maxSearches={10} />)

    expect(screen.getByText('PropGenie')).toBeInTheDocument()
    expect(screen.getByText('Find your perfect property with AI')).toBeInTheDocument()
    expect(screen.getByText('PG')).toBeInTheDocument()
    expect(screen.getByText('4 of 10 searches used today')).toBeInTheDocument()
  })

  it('uses default values when props are omitted', () => {
    render(<ChatHeader />)
    expect(screen.getByText('0 of 50 searches used today')).toBeInTheDocument()
  })
})
