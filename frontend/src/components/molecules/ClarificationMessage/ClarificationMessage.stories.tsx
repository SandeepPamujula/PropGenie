import type { Meta, StoryObj } from '@storybook/react'
import { ClarificationMessage } from './ClarificationMessage'

const meta: Meta<typeof ClarificationMessage> = {
  title: 'Molecules/ClarificationMessage',
  component: ClarificationMessage,
  tags: ['autodocs'],
}
export default meta

type Story = StoryObj<typeof ClarificationMessage>

export const RoundOneNoResolved: Story = {
  args: {
    question: 'Could you please clarify whether you want to buy or rent a property?',
    round: 1,
    maxRounds: 3,
    resolvedFields: {},
  },
}

export const RoundTwoWithResolved: Story = {
  args: {
    question: 'What is your preferred BHK size and maximum monthly budget for the rent?',
    round: 2,
    maxRounds: 3,
    resolvedFields: {
      intent: 'rent',
      city: 'Bangalore',
      location_anchor: 'Indiranagar',
      property_type: 'apartment',
    },
  },
}

export const RoundThreeNearlyComplete: Story = {
  args: {
    question:
      'Are you okay with expanding your search radius to 5 km if we cannot find matching properties?',
    round: 3,
    maxRounds: 3,
    resolvedFields: {
      intent: 'rent',
      city: 'Mumbai',
      location_anchor: 'Bandra West',
      property_type: 'apartment',
      bhk: 3,
      budget_max: 150000,
    },
  },
}
