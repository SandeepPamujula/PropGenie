import { render, screen } from '@testing-library/react'
import { ChatLayout } from './ChatLayout'

// Mock scrollIntoView since JSDOM does not implement it
const mockScrollIntoView = jest.fn()
window.HTMLElement.prototype.scrollIntoView = mockScrollIntoView

describe('ChatLayout', () => {
  beforeEach(() => {
    mockScrollIntoView.mockClear()
  })

  it('renders header, input bar, and children correctly', () => {
    render(
      <ChatLayout
        header={<div data-testid="test-header">Header</div>}
        inputBar={<div data-testid="test-input">Input</div>}
      >
        <div data-testid="test-child">Message</div>
      </ChatLayout>,
    )

    expect(screen.getByTestId('test-header')).toBeInTheDocument()
    expect(screen.getByTestId('test-input')).toBeInTheDocument()
    expect(screen.getByTestId('test-child')).toBeInTheDocument()
    expect(mockScrollIntoView).toHaveBeenCalledTimes(1)
  })

  it('scrolls to bottom when children change', () => {
    const { rerender } = render(
      <ChatLayout header={<div>Header</div>} inputBar={<div>Input</div>}>
        <div>Message 1</div>
      </ChatLayout>,
    )

    expect(mockScrollIntoView).toHaveBeenCalledTimes(1)

    rerender(
      <ChatLayout header={<div>Header</div>} inputBar={<div>Input</div>}>
        <div>Message 1</div>
        <div>Message 2</div>
      </ChatLayout>,
    )

    expect(mockScrollIntoView).toHaveBeenCalledTimes(2)
  })
})
