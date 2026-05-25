import type { ReactElement } from 'react'
import type { ChatMessage } from '../../../types/domain'
import { ErrorMessage } from '../../ErrorMessage'
import { AgentStatus, type AgentPhase } from '../../molecules/AgentStatus/AgentStatus'
import { ClarificationMessage } from '../../molecules/ClarificationMessage/ClarificationMessage'
import { PortalCardList } from '../../molecules/PortalCardList/PortalCardList'
import { SearchMeta } from '../../molecules/SearchMeta/SearchMeta'

export interface MessageListProps {
  messages: ChatMessage[]
  activeStatus?: {
    phase: AgentPhase
    message: string
  } | null
  onRetry?: () => void
  isWaitingForFirstEvent?: boolean
}

export function MessageList({
  messages,
  activeStatus = null,
  onRetry,
  isWaitingForFirstEvent = false,
}: MessageListProps): ReactElement {
  return (
    <div id="message-list" className="flex flex-col gap-4 w-full">
      {messages.map((message) => {
        const isUser = message.role === 'user'

        if (isUser) {
          return (
            <div
              key={message.id}
              id={`message-${message.id}`}
              className="flex justify-end w-full animate-fade-in"
            >
              <div className="max-w-[85%] sm:max-w-[70%] rounded-2xl bg-brand-500 px-4 py-2.5 text-sm text-white shadow-md dark:bg-brand-600 leading-relaxed break-words">
                {message.content}
              </div>
            </div>
          )
        }

        // Render Assistant message variants
        return (
          <div
            key={message.id}
            id={`message-${message.id}`}
            className="flex justify-start w-full animate-fade-in"
          >
            {message.type === 'error' ? (
              <ErrorMessage
                message={message.content}
                retryable={!!onRetry}
                {...(onRetry ? { onRetry } : {})}
              />
            ) : message.type === 'clarification' ? (
              <ClarificationMessage
                question={message.content}
                round={message.clarificationRound ?? 1}
                maxRounds={message.clarificationMaxRounds}
                resolvedFields={message.resolvedFields}
              />
            ) : (
              <div className="flex flex-col gap-3 w-full">
                {/* Standard assistant message bubble */}
                <div className="max-w-[85%] sm:max-w-[75%] rounded-2xl border border-zinc-200 bg-white px-4 py-3 text-sm text-zinc-800 shadow-sm dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-100 leading-relaxed whitespace-pre-wrap break-words">
                  {message.content}
                </div>

                {/* Render Portal Search Cards */}
                {message.type === 'portal_cards' &&
                  message.portalResults &&
                  message.portalResults.length > 0 && (
                    <PortalCardList cards={message.portalResults} />
                  )}

                {/* Render Search Meta */}
                {message.type === 'portal_cards' && message.searchMeta && (
                  <SearchMeta
                    portalsSearched={message.searchMeta.portalsSearched}
                    portalsReturned={message.searchMeta.portalsReturned}
                    portalsDropped={message.searchMeta.portalsDropped}
                    defaultsApplied={message.searchMeta.defaultsApplied}
                  />
                )}
              </div>
            )}
          </div>
        )
      })}

      {/* Loading Skeleton for Initial Request */}
      {isWaitingForFirstEvent && (
        <div id="message-skeleton" className="flex justify-start w-full animate-fade-in">
          <div className="max-w-[85%] sm:max-w-[75%] rounded-2xl border border-zinc-200 bg-white px-4 py-4 shadow-sm dark:border-zinc-800 dark:bg-zinc-900 w-[280px] flex flex-col gap-3">
            <div className="h-2.5 w-full max-w-[90%] animate-pulse rounded-full bg-zinc-200 dark:bg-zinc-800"></div>
            <div className="h-2.5 w-full max-w-[75%] animate-pulse rounded-full bg-zinc-200 dark:bg-zinc-800"></div>
            <div className="h-2.5 w-full max-w-[85%] animate-pulse rounded-full bg-zinc-200 dark:bg-zinc-800"></div>
          </div>
        </div>
      )}

      {/* Active parsing step status message */}
      {activeStatus && (
        <div id="active-agent-status-container" className="flex justify-start w-full">
          <AgentStatus phase={activeStatus.phase} message={activeStatus.message} />
        </div>
      )}
    </div>
  )
}
