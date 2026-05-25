'use client'

import { useState, type ReactElement } from 'react'
import type { AgentPhase } from '@/components/AgentStatus'
import { ChatHeader } from '@/components/ChatHeader'
import { ChatInput } from '@/components/ChatInput'
import { ChatLayout } from '@/components/ChatLayout'
import { MessageList } from '@/components/MessageList'
import { sendMessage, SessionExpiredError, RateLimitError } from '@/lib/api'
import { consumeSSEStream } from '@/lib/sse'
import type { ChatMessage, PortalResult, SearchMeta } from '@/types/domain'

export default function Home(): ReactElement {
  const [input, setInput] = useState('')
  const [isProcessing, setIsProcessing] = useState(false)
  const [currentSearches, setCurrentSearches] = useState(0)
  const [activeStatus, setActiveStatus] = useState<{
    phase: AgentPhase
    message: string
  } | null>(null)

  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content:
        'Namaste! I am PropGenie, your AI property search assistant. I can help you search for properties to buy or rent across top Indian portals like NoBroker and 99acres.\n\nWhat kind of property are you looking for today? (e.g., "3 BHK for rent in HSR Layout, Bangalore under 50k")',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      type: 'text',
    },
  ])

  const handleSubmit = async (overrideText?: string) => {
    const textToSubmit = overrideText !== undefined ? overrideText : input
    if (!textToSubmit.trim() || isProcessing) return

    if (overrideText === undefined) {
      setInput('')
    }

    setIsProcessing(true)
    setActiveStatus({
      phase: 'orchestrator',
      message: 'Understanding your search query...',
    })

    const userMessage: ChatMessage = {
      id: `msg-user-${Date.now()}`,
      role: 'user',
      content: textToSubmit,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      type: 'text',
    }

    setMessages((prev) => [...prev, userMessage])

    try {
      const stream = await sendMessage(textToSubmit)

      const portalCardsMessageId = `msg-portals-${Date.now()}`
      let portalResults: PortalResult[] = []

      await consumeSSEStream(stream, (payload) => {
        switch (payload.event) {
          case 'agent_status': {
            const data = payload.data
            setActiveStatus({
              phase: data.agent,
              message: data.message,
            })
            break
          }
          case 'clarification': {
            const data = payload.data
            setActiveStatus(null)
            const clarificationMsg: ChatMessage = {
              id: `msg-clarify-${Date.now()}`,
              role: 'assistant',
              content: data.message,
              timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
              type: 'clarification',
              clarificationRound: data.round,
              clarificationMaxRounds: data.max_rounds,
              resolvedFields: data.resolved_fields,
              missingFields: data.missing_fields,
            }
            setMessages((prev) => [...prev, clarificationMsg])
            break
          }
          case 'portal_card': {
            const data = payload.data
            setActiveStatus(null)
            
            // Map priority from data.isPriority or backend's data.priority
            const isPriority = typeof data.isPriority === 'boolean'
              ? data.isPriority
              : (typeof data.priority === 'boolean' ? data.priority : false)
            
            const card: PortalResult = {
              portal: data.portal,
              label: data.label || `${data.portal.charAt(0).toUpperCase()}${data.portal.slice(1)} Link`,
              summary: data.summary,
              url: data.url,
              isPriority,
              notes: data.notes,
            }
            portalResults = [...portalResults, card]

            setMessages((prev) => {
              const existingIdx = prev.findIndex((m) => m.id === portalCardsMessageId)
              const newMsg: ChatMessage = {
                id: portalCardsMessageId,
                role: 'assistant',
                content: 'Here are the listings I found matching your criteria:',
                timestamp: new Date().toLocaleTimeString([], {
                  hour: '2-digit',
                  minute: '2-digit',
                }),
                type: 'portal_cards',
                portalResults: portalResults,
              }
              if (existingIdx >= 0) {
                const copy = [...prev]
                copy[existingIdx] = newMsg
                return copy
              } else {
                return [...prev, newMsg]
              }
            })
            break
          }
          case 'search_meta': {
            const data = payload.data
            const meta: SearchMeta = {
              portalsSearched: data.portals_searched,
              portalsReturned: data.portals_returned,
              portalsDropped: data.portals_dropped || [],
              clarificationRounds: data.clarification_rounds || 0,
              defaultsApplied: data.defaults_applied || [],
            }
            setMessages((prev) => {
              const existingIdx = prev.findIndex((m) => m.id === portalCardsMessageId)
              if (existingIdx >= 0) {
                const copy = [...prev]
                const prevMsg = copy[existingIdx]
                if (prevMsg) {
                  copy[existingIdx] = {
                    ...prevMsg,
                    searchMeta: meta,
                  }
                }
                return copy
              }
              return prev
            })
            break
          }
          case 'error': {
            const data = payload.data
            setActiveStatus(null)
            const errorMsg: ChatMessage = {
              id: `msg-error-${Date.now()}`,
              role: 'assistant',
              content: data.message,
              timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
              type: 'error',
            }
            setMessages((prev) => [...prev, errorMsg])
            break
          }
          case 'done': {
            const data = payload.data
            setCurrentSearches(data.search_count_today)
            setIsProcessing(false)
            setActiveStatus(null)
            break
          }
        }
      })
    } catch (err: unknown) {
      setActiveStatus(null)
      setIsProcessing(false)

      let errMsg = 'A connection error occurred while reaching the server.'
      let type: 'text' | 'error' = 'error'

      if (err instanceof SessionExpiredError) {
        errMsg =
          'Your search session has expired. I have started a new session for you. Please try submitting your query again.'
        type = 'text'
      } else if (err instanceof RateLimitError) {
        errMsg = 'You have reached your daily search limit of 10. Please try again tomorrow.'
        type = 'text'
      } else if (err instanceof Error) {
        errMsg = err.message
      }

      setMessages((prev) => [
        ...prev,
        {
          id: `msg-error-catch-${Date.now()}`,
          role: 'assistant',
          content: errMsg,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          type,
        },
      ])
    }
  }

  const handleRetry = () => {
    const lastUserMsg = [...messages].reverse().find((m) => m.role === 'user')
    if (lastUserMsg) {
      // Remove any error messages from search attempts
      setMessages((prev) => prev.filter((m) => m.type !== 'error'))
      handleSubmit(lastUserMsg.content)
    }
  }

  const header = <ChatHeader currentSearches={currentSearches} maxSearches={10} />

  const inputBar = (
    <ChatInput
      value={input}
      onChange={setInput}
      onSubmit={() => handleSubmit()}
      disabled={isProcessing}
    />
  )

  return (
    <ChatLayout header={header} inputBar={inputBar}>
      <MessageList messages={messages} activeStatus={activeStatus} onRetry={handleRetry} />
    </ChatLayout>
  )
}
