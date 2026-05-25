import type { ReactElement } from 'react'
import type { ChatMessage } from '../../../types/domain'
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
}

export function MessageList({
  messages,
  activeStatus = null,
  onRetry,
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
              <div className="max-w-[85%] sm:max-w-[75%] rounded-2xl border border-red-500/20 bg-red-50/20 p-4 shadow-sm dark:border-red-500/30 dark:bg-red-950/10 w-full">
                <div className="flex items-center gap-2 text-red-800 dark:text-red-400">
                  <svg
                    className="h-5 w-5 shrink-0"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2.5"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                    />
                  </svg>
                  <span className="text-sm font-semibold">Search Failure</span>
                </div>
                <p className="mt-2 text-xs text-red-700/90 dark:text-red-300/90 leading-relaxed">
                  {message.content}
                </p>
                {onRetry && (
                  <button
                    onClick={onRetry}
                    id="retry-search-button"
                    className="mt-3.5 flex items-center gap-1.5 rounded-lg bg-red-600 px-3.5 py-1.5 text-xs font-semibold text-white shadow-md hover:bg-red-700 active:scale-95 transition-all duration-200"
                  >
                    <svg
                      className="h-3.5 w-3.5"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2.5"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        d="M4 4v5h.582m15.356 2A8.001 8.001 0 1121.21 7.89M9 11l3-3 3 3m-3-3v12"
                      />
                    </svg>
                    Retry Search
                  </button>
                )}
              </div>
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

      {/* Active parsing step status message */}
      {activeStatus && (
        <div id="active-agent-status-container" className="flex justify-start w-full">
          <AgentStatus phase={activeStatus.phase} message={activeStatus.message} />
        </div>
      )}
    </div>
  )
}
