import type { Meta, StoryObj } from '@storybook/react'
import { RateLimitBanner } from './RateLimitBanner'

const meta: Meta<typeof RateLimitBanner> = {
  title: 'Molecules/RateLimitBanner',
  component: RateLimitBanner,
  tags: ['autodocs'],
}
export default meta

type Story = StoryObj<typeof RateLimitBanner>

export const Default: Story = {
  args: {
    maxSearches: 10,
  },
}

export const CustomResetTime: Story = {
  args: {
    maxSearches: 10,
    resetTimeIST: '12:00 AM IST on 2026-05-26',
  },
}
