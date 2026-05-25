import type { Meta, StoryObj } from '@storybook/react'
import { useState } from 'react'
import { ChatInput } from './ChatInput'

const meta: Meta<typeof ChatInput> = {
  title: 'Molecules/ChatInput',
  component: ChatInput,
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

type Story = StoryObj<typeof ChatInput>

// Helper wrapper to handle state inside Storybook
const ChatInputWithState = (props: Partial<React.ComponentProps<typeof ChatInput>>) => {
  const [value, setValue] = useState(props.value ?? '')
  return (
    <ChatInput
      {...props}
      value={value}
      onChange={setValue}
      onSubmit={() => {
        props.onSubmit?.()
        setValue('')
      }}
    />
  )
}

export const Default: Story = {
  render: () => <ChatInputWithState onSubmit={() => window.alert('Submitted!')} />,
}

export const Disabled: Story = {
  render: () => (
    <ChatInputWithState
      disabled
      onSubmit={() => {}}
      placeholder="Wait for assistant to respond..."
    />
  ),
}

export const NearLimit: Story = {
  render: () => (
    <ChatInputWithState
      value={'A very long message description for property search in South Mumbai. I want a 3 BHK apartment with balcony and sea view. Budget is around 1.5 Lakhs per month. Close to local transportation and schools...'.repeat(
        6,
      )}
      onSubmit={() => {}}
    />
  ),
}
