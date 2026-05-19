import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ChatInput } from './ChatInput'

describe('ChatInput', () => {
  it('renders input area, counter, and send button correctly', () => {
    render(<ChatInput value="test" onChange={jest.fn()} onSubmit={jest.fn()} />)

    expect(screen.getByRole('textbox')).toBeInTheDocument()
    expect(screen.getByRole('textbox')).toHaveValue('test')
    expect(screen.getByText('4 / 2000')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /send/i })).toBeInTheDocument()
  })

  it('enforces character limit on input changes', async () => {
    const handleChange = jest.fn()
    render(<ChatInput value="" onChange={handleChange} onSubmit={jest.fn()} />)

    const textarea = screen.getByRole('textbox')
    await userEvent.type(textarea, 'a')
    expect(handleChange).toHaveBeenCalledWith('a')
  })

  it('disables input and send button when disabled prop is true', () => {
    render(<ChatInput value="test" onChange={jest.fn()} onSubmit={jest.fn()} disabled />)

    expect(screen.getByRole('textbox')).toBeDisabled()
    expect(screen.getByRole('button', { name: /send/i })).toBeDisabled()
    expect(screen.getByText('PropGenie is searching...')).toBeInTheDocument()
  })

  it('disables send button when input is empty', () => {
    render(<ChatInput value="   " onChange={jest.fn()} onSubmit={jest.fn()} />)
    expect(screen.getByRole('button', { name: /send/i })).toBeDisabled()
  })

  it('triggers onSubmit on send button click', async () => {
    const handleSubmit = jest.fn()
    render(<ChatInput value="some message" onChange={jest.fn()} onSubmit={handleSubmit} />)

    const sendButton = screen.getByRole('button', { name: /send/i })
    await userEvent.click(sendButton)
    expect(handleSubmit).toHaveBeenCalledTimes(1)
  })

  it('triggers onSubmit when Enter key is pressed without Shift', async () => {
    const handleSubmit = jest.fn()
    render(<ChatInput value="some message" onChange={jest.fn()} onSubmit={handleSubmit} />)

    const textarea = screen.getByRole('textbox')
    await userEvent.type(textarea, '{enter}')
    expect(handleSubmit).toHaveBeenCalledTimes(1)
  })

  it('does not trigger onSubmit when Enter key is pressed with Shift', async () => {
    const handleSubmit = jest.fn()
    render(<ChatInput value="some message" onChange={jest.fn()} onSubmit={handleSubmit} />)

    const textarea = screen.getByRole('textbox')
    textarea.focus()
    await userEvent.keyboard('{Shift>}{Enter}{/Shift}')
    expect(handleSubmit).not.toHaveBeenCalled()
  })
})
