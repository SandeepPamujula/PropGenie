import type { Meta, StoryObj } from '@storybook/react'
import { ChatPageTemplate } from './ChatPageTemplate'

const meta: Meta<typeof ChatPageTemplate> = {
  title: 'Templates/ChatPageTemplate',
  component: ChatPageTemplate,
  tags: ['autodocs'],
}
export default meta

type Story = StoryObj<typeof ChatPageTemplate>

export const Default: Story = {
  args: {
    header: <div className="p-4 font-bold">Mock Header</div>,
    chatWindow: (
      <div className="h-64 flex items-center justify-center bg-zinc-100">Mock Chat Window</div>
    ),
    inputBar: <div className="p-4 border-t">Mock Input Bar</div>,
  },
}
