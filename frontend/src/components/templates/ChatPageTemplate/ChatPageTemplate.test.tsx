import { render, screen } from '@testing-library/react'
import { ChatPageTemplate } from './ChatPageTemplate'

describe('ChatPageTemplate', () => {
  it('renders header, chatWindow, and inputBar correctly', () => {
    render(
      <ChatPageTemplate
        header={<div data-testid="mock-header">Header</div>}
        chatWindow={<div data-testid="mock-chat">Chat Area</div>}
        inputBar={<div data-testid="mock-input">Input Area</div>}
      />,
    )

    expect(screen.getByTestId('mock-header')).toBeInTheDocument()
    expect(screen.getByTestId('mock-chat')).toBeInTheDocument()
    expect(screen.getByTestId('mock-input')).toBeInTheDocument()
  })
})
