import type { Meta, StoryObj } from '@storybook/react'
import { PropertyLinkList } from './PropertyLinkList'

const meta: Meta<typeof PropertyLinkList> = {
  title: 'Molecules/PropertyLinkList',
  component: PropertyLinkList,
  tags: ['autodocs'],
}
export default meta

type Story = StoryObj<typeof PropertyLinkList>

export const NoLinks: Story = {
  args: {
    propertyLinks: [],
    portalDisplayName: 'NoBroker',
    portalNameLower: 'nobroker',
    isLoading: false,
  },
}

export const OneLink: Story = {
  args: {
    propertyLinks: [
      {
        url: 'https://nobroker.in/prop-1',
        portal: 'NoBroker',
        rank: 1,
        validation: { schema_valid: true, head_status: 200 },
      },
    ],
    portalDisplayName: 'NoBroker',
    portalNameLower: 'nobroker',
    isLoading: false,
  },
}

export const ThreeLinks: Story = {
  args: {
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
    portalDisplayName: 'NoBroker',
    portalNameLower: 'nobroker',
    isLoading: false,
  },
}

export const FiveLinks: Story = {
  args: {
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
      {
        url: 'https://99acres.com/prop-6',
        portal: '99acres',
        rank: 6,
        validation: { schema_valid: true, head_status: 200 },
      },
    ],
    portalDisplayName: '99acres',
    portalNameLower: '99acres',
    isLoading: false,
  },
}

export const Loading: Story = {
  args: {
    propertyLinks: [],
    portalDisplayName: 'NoBroker',
    portalNameLower: 'nobroker',
    isLoading: true,
  },
}
