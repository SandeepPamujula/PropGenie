'use client'

import { useState, type ReactElement } from 'react'
import { ChatHeader } from '@/components/ChatHeader'
import { ChatInput } from '@/components/ChatInput'
import { ChatLayout } from '@/components/ChatLayout'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: string
}

export default function Home(): ReactElement {
  const [input, setInput] = useState('')
  const [isProcessing, setIsProcessing] = useState(false)
  const [currentSearches, setCurrentSearches] = useState(0)
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content:
        'Namaste! I am PropGenie, your AI property search assistant. I can help you search for properties to buy or rent across top Indian portals like NoBroker and 99acres.\n\nWhat kind of property are you looking for today? (e.g., "3 BHK for rent in HSR Layout, Bangalore under 50k")',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    },
  ])

  const handleSubmit = () => {
    if (!input.trim() || isProcessing) return

    const userMessage: Message = {
      id: `msg-${Date.now()}`,
      role: 'user',
      content: input,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    }

    setMessages((prev) => [...prev, userMessage])
    setInput('')
    setIsProcessing(true)

    // Simulate Agent processing
    setTimeout(() => {
      const botMessage: Message = {
        id: `msg-${Date.now() + 1}`,
        role: 'assistant',
        content: `I received your query: "${userMessage.content}".\n\nI am currently searching top Indian property portals. (Note: Full agent API integration will be implemented in subsequent user stories).`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      }
      setMessages((prev) => [...prev, botMessage])
      setIsProcessing(false)
      setCurrentSearches((prev) => Math.min(prev + 1, 10))
    }, 1500)
  }

  const header = <ChatHeader currentSearches={currentSearches} maxSearches={10} />

  const inputBar = (
    <ChatInput value={input} onChange={setInput} onSubmit={handleSubmit} disabled={isProcessing} />
  )

  return (
    <ChatLayout header={header} inputBar={inputBar}>
      <div className="flex flex-col gap-4 py-2" role="log" aria-live="polite">
        {messages.map((msg) => (
          <div
            key={msg.id}
            id={msg.id}
            className={`flex w-full flex-col gap-1.5 animate-fade-in ${
              msg.role === 'user' ? 'items-end' : 'items-start'
            }`}
          >
            {/* Sender bubble */}
            <div
              className={`max-w-[85%] rounded-2xl px-4 py-2.5 text-sm shadow-sm md:max-w-[75%] ${
                msg.role === 'user'
                  ? 'bg-brand-500 text-white rounded-tr-none'
                  : 'glass-card rounded-tl-none text-zinc-800 dark:text-zinc-100'
              }`}
            >
              <p className="whitespace-pre-line leading-relaxed font-sans">{msg.content}</p>
            </div>

            {/* Timestamp */}
            <span className="px-2 text-[10px] text-zinc-400 select-none dark:text-zinc-500 font-sans">
              {msg.timestamp}
            </span>
          </div>
        ))}
      </div>
    </ChatLayout>
  )
}
