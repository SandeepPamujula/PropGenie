import type { ReactElement } from 'react'

export type AgentPhase =
  | 'orchestrator'
  | 'clarification'
  | 'query_builder'
  | 'url_validator'
  | 'response_formatter'
  | 'complete'

export interface AgentStatusProps {
  phase: AgentPhase
  message: string
  isComplete?: boolean
}

export function AgentStatus({
  phase,
  message,
  isComplete = false,
}: AgentStatusProps): ReactElement {
  const getPhaseLabel = (p: AgentPhase) => {
    switch (p) {
      case 'orchestrator':
        return 'Orchestrator'
      case 'clarification':
        return 'Clarifier'
      case 'query_builder':
        return 'Query Builder'
      case 'url_validator':
        return 'URL Validator'
      case 'response_formatter':
        return 'Formatter'
      case 'complete':
        return 'Complete'
    }
  }

  return (
    <div
      id={`agent-status-${phase}`}
      className="flex items-center gap-3 rounded-xl border border-zinc-200/50 bg-zinc-50/50 p-3 shadow-sm transition-all duration-300 dark:border-zinc-800/50 dark:bg-zinc-900/30 w-fit max-w-full animate-fade-in"
    >
      {/* Visual Indicator: Bouncing Pulse or Green Checkmark */}
      <div className="flex h-5 w-5 shrink-0 items-center justify-center">
        {isComplete ? (
          <div
            id="status-indicator-complete"
            className="flex h-4 w-4 items-center justify-center rounded-full bg-emerald-500 text-white animate-scale-in"
          >
            <svg
              className="h-3 w-3"
              fill="none"
              stroke="currentColor"
              strokeWidth="3"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
            </svg>
          </div>
        ) : (
          <span className="relative flex h-3 w-3">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-brand-500 opacity-75"></span>
            <span className="relative inline-flex h-3 w-3 rounded-full bg-brand-500"></span>
          </span>
        )}
      </div>

      {/* Message Text */}
      <div className="flex flex-col pr-1 min-w-0">
        <span
          id="status-message-text"
          className="truncate text-xs font-semibold text-zinc-700 dark:text-zinc-300"
        >
          {message}
        </span>
        <span
          id="status-phase-label"
          className="text-[10px] font-medium text-zinc-400 dark:text-zinc-500"
        >
          {getPhaseLabel(phase)}
        </span>
      </div>
    </div>
  )
}
