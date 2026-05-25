import { render, screen, fireEvent } from '@testing-library/react'
import { MessageList } from './MessageList'

describe('MessageList', () => {
  it('renders user and assistant text messages correctly', () => {
    render(
      <MessageList
        messages={[
          {
            id: '1',
            role: 'user',
            content: 'User test message',
            timestamp: '10:00 pm',
          },
          {
            id: '2',
            role: 'assistant',
            content: 'Assistant test message',
            timestamp: '10:01 pm',
            type: 'text',
          },
        ]}
      />,
    )

    expect(screen.getByText('User test message')).toBeInTheDocument()
    expect(screen.getByText('Assistant test message')).toBeInTheDocument()
  })

  it('renders clarification message component with correct props', () => {
    render(
      <MessageList
        messages={[
          {
            id: '1',
            role: 'assistant',
            content: 'Is this for rent or buy?',
            timestamp: '10:00 pm',
            type: 'clarification',
            clarificationRound: 2,
            resolvedFields: { city: 'Pune' },
          },
        ]}
      />,
    )

    expect(screen.getByText('Clarification Round 2 of 3')).toBeInTheDocument()
    expect(screen.getByText('Is this for rent or buy?')).toBeInTheDocument()
    expect(screen.getByText('Resolved Parameters')).toBeInTheDocument()
  })

  it('renders failure message with active retry button', () => {
    const handleRetry = jest.fn()
    render(
      <MessageList
        messages={[
          {
            id: '1',
            role: 'assistant',
            content: 'A connection error occurred',
            timestamp: '10:00 pm',
            type: 'error',
          },
        ]}
        onRetry={handleRetry}
      />,
    )

    expect(screen.getByText('A connection error occurred')).toBeInTheDocument()

    const retryBtn = screen.getByRole('button', { name: /Retry Search/i })
    expect(retryBtn).toBeInTheDocument()

    fireEvent.click(retryBtn)
    expect(handleRetry).toHaveBeenCalledTimes(1)
  })

  it('renders active status loader at the end when activeStatus is passed', () => {
    render(
      <MessageList
        messages={[
          {
            id: '1',
            role: 'user',
            content: 'Hello',
            timestamp: '10:00 pm',
          },
        ]}
        activeStatus={{
          phase: 'url_validator',
          message: 'Validating links...',
        }}
      />,
    )

    expect(screen.getByText('Hello')).toBeInTheDocument()
    expect(screen.getByText('Validating links...')).toBeInTheDocument()
    expect(screen.getByText('URL Validator')).toBeInTheDocument()
  })
})
