import { render, screen, fireEvent } from '@testing-library/react'
import { ErrorMessage } from './ErrorMessage'

describe('ErrorMessage', () => {
  it('renders the message text correctly', () => {
    render(<ErrorMessage message="Test error message" />)
    expect(screen.getByText('Test error message')).toBeInTheDocument()
  })

  it('renders retry button and calls onRetry when retryable is true', () => {
    const handleRetry = jest.fn()
    render(<ErrorMessage message="Retry me" retryable onRetry={handleRetry} />)
    
    const button = screen.getByRole('button', { name: /retry search/i })
    expect(button).toBeInTheDocument()
    
    fireEvent.click(button)
    expect(handleRetry).toHaveBeenCalledTimes(1)
  })

  it('does not render retry button when retryable is false', () => {
    render(<ErrorMessage message="Fatal error" retryable={false} />)
    expect(screen.queryByRole('button', { name: /retry search/i })).not.toBeInTheDocument()
  })
})
