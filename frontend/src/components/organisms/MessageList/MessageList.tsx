import type { ReactElement } from 'react'
import type { ChatMessage } from '../../../types/domain'
import { AgentStatus, type AgentPhase } from '../../molecules/AgentStatus/AgentStatus'
import { ClarificationMessage } from '../../molecules/ClarificationMessage/ClarificationMessage'

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

                {/* Render Portal Search Cards (will be styled natively in US-20) */}
                {message.type === 'portal_cards' &&
                  message.portalResults &&
                  message.portalResults.length > 0 && (
                    <div
                      id={`portal-cards-${message.id}`}
                      className="grid grid-cols-1 gap-3 sm:grid-cols-2 mt-1 w-full max-w-xl animate-fade-in"
                    >
                      {message.portalResults.map((card, idx) => {
                        const getPortalColorClass = (portalName: string) => {
                          switch (portalName.toLowerCase()) {
                            case 'nobroker':
                              return 'text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-950/20 border-amber-200/50 dark:border-amber-900/30'
                            case '99acres':
                              return 'text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-950/20 border-blue-200/50 dark:border-blue-900/30'
                            case 'magicbricks':
                              return 'text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-950/20 border-red-200/50 dark:border-red-900/30'
                            case 'housing':
                              return 'text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/20 border-emerald-200/50 dark:border-emerald-900/30'
                            default:
                              return 'text-zinc-600 dark:text-zinc-400 bg-zinc-50 dark:bg-zinc-950/20 border-zinc-200/50 dark:border-zinc-900/30'
                          }
                        }

                        return (
                          <div
                            key={idx}
                            className="flex flex-col justify-between p-3.5 rounded-xl border border-zinc-200 bg-white shadow-sm dark:border-zinc-800 dark:bg-zinc-900/50"
                          >
                            <div>
                              <span
                                className={`inline-block px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider border ${getPortalColorClass(
                                  card.portal,
                                )}`}
                              >
                                {card.portal}
                              </span>
                              <h4 className="text-xs font-bold text-zinc-800 dark:text-zinc-200 mt-2 line-clamp-1">
                                {card.label}
                              </h4>
                              <p className="text-[11px] text-zinc-500 dark:text-zinc-400 mt-1 line-clamp-2 leading-normal">
                                {card.summary}
                              </p>
                            </div>
                            <div className="mt-3.5 pt-2.5 border-t border-zinc-100 dark:border-zinc-800/80">
                              <a
                                href={card.url}
                                target="_blank"
                                rel="noreferrer"
                                className="flex items-center justify-between text-xs font-bold text-brand-500 hover:text-brand-600 transition-colors"
                              >
                                <span>View Listings</span>
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
                                    d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
                                  />
                                </svg>
                              </a>
                            </div>
                          </div>
                        )
                      })}
                    </div>
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
