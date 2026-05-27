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

      {/* Loading Skeleton when Property Scraper is active */}
      {activeStatus?.phase === 'property_scraper' && (
        <div id="scraper-skeleton" className="flex flex-col gap-4 w-full animate-fade-in mb-3">
          {/* Skeleton message bubble */}
          <div className="max-w-[85%] sm:max-w-[75%] rounded-2xl border border-zinc-200 bg-white px-4 py-3.5 shadow-sm dark:border-zinc-800 dark:bg-zinc-900 w-[320px] flex flex-col gap-2">
            <div className="h-3 w-11/12 animate-pulse rounded bg-zinc-200 dark:bg-zinc-800"></div>
            <div className="h-3 w-8/12 animate-pulse rounded bg-zinc-200 dark:bg-zinc-800"></div>
          </div>
          
          {/* Skeleton Cards Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-2.5 w-full max-w-2xl">
            {[1, 2].map((i) => (
              <div
                key={i}
                className="glass-card flex flex-col justify-between p-4 rounded-xl shadow-sm border border-zinc-200 dark:border-zinc-800/80 bg-white dark:bg-zinc-900 w-full"
              >
                <div>
                  <div className="flex items-center justify-between mb-3 w-full">
                    <div className="h-4 w-16 animate-pulse rounded bg-zinc-200 dark:bg-zinc-800"></div>
                    <div className="h-4 w-20 animate-pulse rounded bg-zinc-200 dark:bg-zinc-800"></div>
                  </div>
                  <div className="h-4 w-5/6 animate-pulse rounded bg-zinc-200 dark:bg-zinc-800 mb-2"></div>
                  <div className="h-3 w-full animate-pulse rounded bg-zinc-200 dark:bg-zinc-800 mb-1.5"></div>
                  <div className="h-3 w-2/3 animate-pulse rounded bg-zinc-200 dark:bg-zinc-800"></div>
                </div>
                
                <div className="mt-4 pt-3 border-t border-zinc-100 dark:border-zinc-800/80">
                  <div className="h-8 w-full animate-pulse rounded-lg bg-zinc-200 dark:bg-zinc-800 mb-3.5"></div>
                  
                  {/* Shimmering Property Links Skeleton */}
                  <div className="border-t border-dashed border-zinc-200 dark:border-zinc-800/60 pt-3 flex flex-col gap-2.5">
                    <div className="h-2.5 w-1/3 animate-pulse rounded bg-zinc-200 dark:bg-zinc-800 mb-1"></div>
                    {[1, 2, 3].map((j) => (
                      <div key={j} className="flex items-center gap-2">
                        <div className="h-5 w-5 animate-pulse rounded bg-zinc-200 dark:bg-zinc-800"></div>
                        <div className="h-3 flex-1 animate-pulse rounded bg-zinc-200 dark:bg-zinc-800"></div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            ))}
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
