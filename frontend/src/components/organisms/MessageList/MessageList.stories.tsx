import type { Meta, StoryObj } from '@storybook/react'
import { MessageList } from './MessageList'

const meta: Meta<typeof MessageList> = {
  title: 'Organisms/MessageList',
  component: MessageList,
  tags: ['autodocs'],
  decorators: [
    (Story) => (
      <div className="max-w-xl mx-auto p-4 border border-zinc-200 rounded-lg dark:border-zinc-800">
        <Story />
      </div>
    ),
  ],
}
export default meta

type Story = StoryObj<typeof MessageList>

export const EmptyWithStatus: Story = {
  args: {
    messages: [],
    activeStatus: {
      phase: 'orchestrator',
      message: 'Classifying search parameters...',
    },
  },
}

export const ConversationHistory: Story = {
  args: {
    messages: [
      {
        id: '1',
        role: 'user',
        content: 'Hi, I want a 3 BHK rent in Indiranagar under 50k',
        timestamp: '10:00 pm',
        type: 'text',
      },
      {
        id: '2',
        role: 'assistant',
        content: 'I have classified your query and extracted Indiranagar, Rent, 3 BHK.',
        timestamp: '10:01 pm',
        type: 'text',
      },
      {
        id: '3',
        role: 'assistant',
        content: 'Please confirm your search criteria:',
        timestamp: '10:01 pm',
        type: 'clarification',
        clarificationRound: 1,
        clarificationMaxRounds: 3,
        resolvedFields: {
          intent: 'rent',
          city: 'Bangalore',
          location_anchor: 'Indiranagar',
          bhk: 3,
          budget_max: 50000,
        },
      },
    ],
  },
}

export const FailureStateWithRetry: Story = {
  args: {
    messages: [
      {
        id: '1',
        role: 'user',
        content: 'Find apartments in Indiranagar',
        timestamp: '10:00 pm',
      },
      {
        id: '2',
        role: 'assistant',
        content:
          'Failed to establish connection with the property search engine. Please check your network and retry.',
        timestamp: '10:01 pm',
        type: 'error',
      },
    ],
    onRetry: () => window.alert('Retrying search!'),
  },
}
