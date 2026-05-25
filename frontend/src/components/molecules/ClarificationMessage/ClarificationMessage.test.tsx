import { render, screen } from '@testing-library/react'
import { ClarificationMessage } from './ClarificationMessage'

describe('ClarificationMessage', () => {
  it('renders round indicator and question text', () => {
    render(
      <ClarificationMessage
        question="Which locality in Indiranagar are you looking at?"
        round={2}
        maxRounds={3}
      />,
    )

    expect(screen.getByText('Clarification Round 2 of 3')).toBeInTheDocument()
    expect(
      screen.getByText('Which locality in Indiranagar are you looking at?'),
    ).toBeInTheDocument()
    expect(screen.queryByText('Resolved Parameters')).not.toBeInTheDocument()
  })

  it('renders and formats resolved parameters as tags', () => {
    render(
      <ClarificationMessage
        question="What budget limit do you have?"
        round={1}
        resolvedFields={{
          intent: 'rent',
          city: 'Mumbai',
          bhk: 3,
          budget_max: 120000,
        }}
      />,
    )

    expect(screen.getByText('Resolved Parameters')).toBeInTheDocument()

    // check chips and labels
    expect(screen.getByText('Intent:')).toBeInTheDocument()
    expect(screen.getByText('Rent')).toBeInTheDocument()

    expect(screen.getByText('City:')).toBeInTheDocument()
    expect(screen.getByText('Mumbai')).toBeInTheDocument()

    expect(screen.getByText('BHK:')).toBeInTheDocument()
    expect(screen.getByText('3 BHK')).toBeInTheDocument()

    expect(screen.getByText('Max Budget:')).toBeInTheDocument()
    expect(screen.getByText('₹1.2 L')).toBeInTheDocument() // 120000 format
  })
})
