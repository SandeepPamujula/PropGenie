import type { Meta, StoryObj } from '@storybook/react'
import { ChatHeader } from './ChatHeader'

const meta: Meta<typeof ChatHeader> = {
  title: 'Molecules/ChatHeader',
  component: ChatHeader,
  tags: ['autodocs'],
}
export default meta

type Story = StoryObj<typeof ChatHeader>

export const Default: Story = {
  args: {
    currentSearches: 3,
    maxSearches: 10,
  },
}

export const ZeroSearches: Story = {
  args: {
    currentSearches: 0,
    maxSearches: 10,
  },
}

export const LimitReached: Story = {
  args: {
    currentSearches: 10,
    maxSearches: 10,
  },
}
