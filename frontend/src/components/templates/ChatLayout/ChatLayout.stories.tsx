import type { Meta, StoryObj } from '@storybook/react'
import { ChatLayout } from './ChatLayout'

const meta: Meta<typeof ChatLayout> = {
  title: 'Templates/ChatLayout',
  component: ChatLayout,
  tags: ['autodocs'],
}
export default meta

type Story = StoryObj<typeof ChatLayout>

export const Default: Story = {
  args: {
    header: (
      <div className="p-4 bg-blue-50 dark:bg-blue-950 font-bold text-center">Header Content</div>
    ),
    inputBar: (
      <div className="p-4 bg-zinc-100 dark:bg-zinc-800 text-center rounded-xl">Input Area</div>
    ),
    children: (
      <div className="flex flex-col gap-3">
        {Array.from({ length: 15 }).map((_, i) => (
          <div
            key={i}
            className={`p-4 rounded-xl max-w-sm ${
              i % 2 === 0
                ? 'bg-brand-500 text-white self-end'
                : 'bg-zinc-100 dark:bg-zinc-800 self-start'
            }`}
          >
            Message number {i + 1}
          </div>
        ))}
      </div>
    ),
  },
}
