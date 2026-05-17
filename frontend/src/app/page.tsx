'use client'

import { useState } from 'react'
import { ChatPageTemplate } from '@/components/templates/ChatPageTemplate/ChatPageTemplate'

export default function Home() {
  const [input, setInput] = useState('')

  const handleSend = (e: React.FormEvent) => {
    e.preventDefault()
    // Placeholder logic for sending message
    if (input.trim()) {
      setInput('')
    }
  }

  const header = (
    <div className="flex w-full items-center justify-between px-4 py-3 sm:px-6">
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-tr from-brand-500 to-brand-900 text-white shadow-md">
          {/* Mock Logo Icon */}
          <span className="font-bold">PG</span>
        </div>
        <div>
          <h1 className="text-lg font-bold tracking-tight text-zinc-900 dark:text-white">
            PropGenie
          </h1>
          <p className="text-xs text-zinc-500 dark:text-zinc-400">
            Find your perfect Indian property with AI
          </p>
        </div>
      </div>
    </div>
  )

  const chatWindow = (
    <div className="flex h-full flex-col items-center justify-center py-20 text-center opacity-50">
      <p className="text-lg font-medium text-zinc-600 dark:text-zinc-400">
        Conversation Area (Placeholder)
      </p>
      <p className="text-sm text-zinc-500 dark:text-zinc-500 mt-2">
        Messages will appear here once the chat components are built.
      </p>
    </div>
  )

  const inputBar = (
    <form onSubmit={handleSend} className="relative flex items-center">
      <input
        id="chat-input"
        type="text"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        placeholder="Ask for rentals or sale properties..."
        className="w-full rounded-2xl border border-zinc-200/80 bg-zinc-50/50 py-3.5 pl-4 pr-14 text-sm outline-none transition duration-300 focus:border-brand-500/70 focus:bg-white focus:ring-4 focus:ring-brand-500/10 dark:border-zinc-800/80 dark:bg-zinc-900/50 dark:focus:border-brand-500/60 dark:focus:bg-zinc-950 dark:focus:ring-brand-500/5"
      />
      <button
        id="send-button"
        type="submit"
        disabled={!input.trim()}
        className="absolute right-2 flex h-10 w-10 items-center justify-center rounded-xl bg-brand-500 text-white shadow-md transition duration-300 hover:bg-brand-900 disabled:bg-zinc-200 disabled:text-zinc-400 dark:disabled:bg-zinc-800 dark:disabled:text-zinc-600"
      >
        <svg
          className="h-5 w-5 transform rotate-90"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2.5}
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 19l9-7-9-7v14z" />
        </svg>
      </button>
    </form>
  )

  return <ChatPageTemplate header={header} chatWindow={chatWindow} inputBar={inputBar} />
}
