'use client'

import { useState, useEffect, type ReactElement } from 'react'
import type { AgentPhase } from '@/components/AgentStatus'
import { ChatHeader } from '@/components/ChatHeader'
import { ChatInput } from '@/components/ChatInput'
import { ChatLayout } from '@/components/ChatLayout'
import { MessageList } from '@/components/MessageList'
import { RateLimitBanner } from '@/components/RateLimitBanner'
import { sendMessage, SessionExpiredError, RateLimitError } from '@/lib/api'
import { getSessionId, resetSessionId } from '@/lib/session'
import { consumeSSEStream } from '@/lib/sse'
import type { ChatMessage, PortalResult, SearchMeta } from '@/types/domain'

export default function Home(): ReactElement {
  const [input, setInput] = useState('')
  const [isProcessing, setIsProcessing] = useState(false)
  const [isOnline, setIsOnline] = useState(true)

  useEffect(() => {
    // Generate/initialize a fresh session ID on page load/refresh to keep UI and backend state synchronized
    resetSessionId()

    // eslint-disable-next-line react-hooks/set-state-in-effect
    setIsOnline(navigator.onLine)
    const handleOnline = () => setIsOnline(true)
    const handleOffline = () => setIsOnline(false)
    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)
    return () => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
    }
  }, [])

  const [currentSearches, setCurrentSearches] = useState(0)
  const [isRateLimited, setIsRateLimited] = useState(false)
  const [activeStatus, setActiveStatus] = useState<{
    phase: AgentPhase
    message: string
  } | null>(null)
  const [isWaitingForFirstEvent, setIsWaitingForFirstEvent] = useState(false)

  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content:
        'Namaste! I am PropGenie, your AI property search assistant. I can help you search for properties to buy or rent across top Indian portals like NoBroker and 99acres.\n\nWhat kind of property are you looking for today? (e.g., "3 BHK for rent in Indiranagar, Bangalore beween 30k to 50k")',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      type: 'text',
    },
  ])

  const handleSubmitWithRetry = async (
    textToSubmit: string,
    portalCardsMessageId: string,
    attempt = 1
  ) => {
    try {
      const stream = await sendMessage(textToSubmit)
      let portalResults: PortalResult[] = []
      let clarificationReceived = false

      await consumeSSEStream(stream, (payload) => {
        setIsWaitingForFirstEvent(false)

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
            clarificationReceived = true
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

            const isPriority =
              typeof data.isPriority === 'boolean'
                ? data.isPriority
                : typeof data.priority === 'boolean'
                  ? data.priority
                  : false

            const card: PortalResult = {
              portal: data.portal,
              label:
                data.label || `${data.portal.charAt(0).toUpperCase()}${data.portal.slice(1)} Link`,
              summary: data.summary,
              url: data.url,
              isPriority,
              ...(data.notes !== undefined ? { notes: data.notes } : {}),
              propertyLinks: data.property_links || [],
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
              propertyLinksCount: data.property_links_count || 0,
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
            if (data.search_count_today >= data.search_limit) {
              setIsRateLimited(true)
            }
            setIsProcessing(false)
            setActiveStatus(null)

            if (portalResults.length === 0 && !clarificationReceived) {
              setMessages((prev) => [
                ...prev,
                {
                  id: `msg-empty-${Date.now()}`,
                  role: 'assistant',
                  content: 'No portals returned results for your search. Try adjusting your criteria.',
                  timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
                  type: 'text',
                },
              ])
            }
            break
          }
        }
      })
    } catch (err: unknown) {
      if (err instanceof RateLimitError) {
        setIsRateLimited(true)
        setCurrentSearches(10)
        setIsProcessing(false)
        setActiveStatus(null)
        setIsWaitingForFirstEvent(false)
        return
      }

      if (err instanceof SessionExpiredError) {
        setIsProcessing(false)
        setActiveStatus(null)
        setIsWaitingForFirstEvent(false)
        setMessages((prev) => [
          ...prev,
          {
            id: `msg-session-${Date.now()}`,
            role: 'assistant',
            content:
              'Your search session has expired. I have started a new session for you. Please try submitting your query again.',
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
            type: 'text',
          },
        ])
        return
      }

      if (attempt <= 3) {
        // Retry logic with exponential backoff
        setActiveStatus({
          phase: 'orchestrator',
          message: `Connection lost. Retrying (Attempt ${attempt} of 3)...`,
        })
        const delay = Math.pow(2, attempt) * 1000
        await new Promise((res) => setTimeout(res, delay))
        await handleSubmitWithRetry(textToSubmit, portalCardsMessageId, attempt + 1)
      } else {
        // Max retries exceeded
        setIsProcessing(false)
        setActiveStatus(null)
        setIsWaitingForFirstEvent(false)

        let errMsg = 'A connection error occurred while reaching the server.'
        if (err instanceof Error) {
          errMsg = err.message
        }

        setMessages((prev) => [
          ...prev,
          {
            id: `msg-error-catch-${Date.now()}`,
            role: 'assistant',
            content: errMsg,
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
            type: 'error',
          },
        ])
      }
    }
  }

  const handleSubmit = async (overrideText?: string) => {
    const textToSubmit = overrideText !== undefined ? overrideText : input
    if (!textToSubmit.trim() || isProcessing) return

    if (overrideText === undefined) {
      setInput('')
    }

    setIsProcessing(true)
    setIsWaitingForFirstEvent(true)
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

    const portalCardsMessageId = `msg-portals-${Date.now()}`
    await handleSubmitWithRetry(textToSubmit, portalCardsMessageId, 1)
  }

  const handleRetry = () => {
    const lastUserMsg = [...messages].reverse().find((m) => m.role === 'user')
    if (lastUserMsg) {
      setMessages((prev) => prev.filter((m) => m.type !== 'error'))
      handleSubmit(lastUserMsg.content)
    }
  }

  const header = (
    <div className="flex flex-col w-full">
      {!isOnline && (
        <div
          id="offline-banner"
          className="w-full bg-red-600 px-4 py-2 text-center text-sm font-medium text-white shadow-sm dark:bg-red-700 animate-fade-in"
        >
          You are currently offline. Please check your internet connection.
        </div>
      )}
      <ChatHeader currentSearches={currentSearches} maxSearches={10} />
    </div>
  )

  const inputBar = (
    <div className="flex flex-col gap-3 w-full animate-fade-in">
      {isRateLimited && <RateLimitBanner maxSearches={10} />}
      <ChatInput
        value={input}
        onChange={setInput}
        onSubmit={() => handleSubmit()}
        disabled={isProcessing || isRateLimited || !isOnline}
        {...(isRateLimited
          ? { placeholder: 'Daily search limit reached. Resets at midnight IST.' }
          : !isOnline
            ? { placeholder: 'You are offline.' }
            : {})}
      />
    </div>
  )

  return (
    <ChatLayout header={header} inputBar={inputBar}>
      <MessageList
        messages={messages}
        activeStatus={activeStatus}
        onRetry={handleRetry}
        isWaitingForFirstEvent={isWaitingForFirstEvent}
      />
    </ChatLayout>
  )
}
