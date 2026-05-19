import type { Meta, StoryObj } from '@storybook/react'
import { AgentStatus } from './AgentStatus'

const meta: Meta<typeof AgentStatus> = {
  title: 'Molecules/AgentStatus',
  component: AgentStatus,
  tags: ['autodocs'],
}
export default meta

type Story = StoryObj<typeof AgentStatus>

export const OrchestratorRunning: Story = {
  args: {
    phase: 'orchestrator',
    message: 'Understanding your search...',
    isComplete: false,
  },
}

export const QueryBuilderRunning: Story = {
  args: {
    phase: 'query_builder',
    message: 'Building portal search queries...',
    isComplete: false,
  },
}

export const UrlValidatorRunning: Story = {
  args: {
    phase: 'url_validator',
    message: 'Validating search URLs...',
    isComplete: false,
  },
}

export const PhaseComplete: Story = {
  args: {
    phase: 'complete',
    message: 'Search query processed successfully!',
    isComplete: true,
  },
}
