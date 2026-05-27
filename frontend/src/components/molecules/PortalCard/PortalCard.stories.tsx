import type { Meta, StoryObj } from '@storybook/react'
import { PortalCard } from './PortalCard'
import type { PortalResult } from '../../../types/domain'

const meta: Meta<typeof PortalCard> = {
  title: 'Molecules/PortalCard',
  component: PortalCard,
  tags: ['autodocs'],
}
export default meta

type Story = StoryObj<typeof PortalCard>

const baseCard: PortalResult = {
  portal: 'nobroker',
  label: '3 BHK HSR Layout Flat',
  summary: '3BHK rentals near HSR Layout, Bangalore — ₹30K to ₹40K/mo',
  url: 'https://www.nobroker.in/property/rent/bangalore/Hsr-layout',
  isPriority: true,
  notes: '4 km radius applied',
}

export const NoLinks: Story = {
  args: {
    card: {
      ...baseCard,
      propertyLinks: [],
    },
  },
}

export const OneLink: Story = {
  args: {
    card: {
      ...baseCard,
      propertyLinks: [
        {
          url: 'https://nobroker.in/prop-1',
          portal: 'NoBroker',
          rank: 1,
          validation: { schema_valid: true, head_status: 200 },
        },
      ],
    },
  },
}

export const ThreeLinks: Story = {
  args: {
    card: {
      ...baseCard,
      propertyLinks: [
        {
          url: 'https://nobroker.in/prop-1',
          portal: 'NoBroker',
          rank: 1,
          validation: { schema_valid: true, head_status: 200 },
        },
        {
          url: 'https://nobroker.in/prop-2',
          portal: 'NoBroker',
          rank: 2,
          validation: { schema_valid: true, head_status: 200 },
        },
        {
          url: 'https://nobroker.in/prop-3',
          portal: 'NoBroker',
          rank: 3,
          validation: { schema_valid: true, head_status: 200 },
        },
      ],
    },
  },
}

export const FiveLinks: Story = {
  args: {
    card: {
      ...baseCard,
      portal: '99acres',
      label: 'Plots in Indiranagar',
      summary: 'Plots for sale near Indiranagar, Bangalore — ₹1Cr to ₹10Cr',
      url: 'https://www.99acres.com/indiranagar-bangalore',
      isPriority: true,
      propertyLinks: [
        {
          url: 'https://99acres.com/prop-1',
          portal: '99acres',
          rank: 1,
          validation: { schema_valid: true, head_status: 200 },
        },
        {
          url: 'https://99acres.com/prop-2',
          portal: '99acres',
          rank: 2,
          validation: { schema_valid: true, head_status: 200 },
        },
        {
          url: 'https://99acres.com/prop-3',
          portal: '99acres',
          rank: 3,
          validation: { schema_valid: true, head_status: 200 },
        },
        {
          url: 'https://99acres.com/prop-4',
          portal: '99acres',
          rank: 4,
          validation: { schema_valid: true, head_status: 200 },
        },
        {
          url: 'https://99acres.com/prop-5',
          portal: '99acres',
          rank: 5,
          validation: { schema_valid: true, head_status: 200 },
        },
      ],
    },
  },
}
