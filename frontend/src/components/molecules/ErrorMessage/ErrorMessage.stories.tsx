import type { Meta, StoryObj } from '@storybook/react'
import { ErrorMessage } from './ErrorMessage'

const meta = {
  title: 'Molecules/ErrorMessage',
  component: ErrorMessage,
  parameters: {
    layout: 'padded',
  },
  tags: ['autodocs'],
} satisfies Meta<typeof ErrorMessage>

export default meta
type Story = StoryObj<typeof meta>

export const Retryable: Story = {
  args: {
    message: 'Connection lost while searching. Please check your network and try again.',
    retryable: true,
  },
}

export const NonRetryable: Story = {
  args: {
    message: 'An unexpected error occurred. Please refresh the page.',
    retryable: false,
  },
}
