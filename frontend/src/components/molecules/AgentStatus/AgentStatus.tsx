import { useState, type ReactElement } from 'react'
import { WorkflowGraph } from '../WorkflowGraph/WorkflowGraph'

export type AgentPhase =
  | 'orchestrator'
  | 'clarification'
  | 'query_builder'
  | 'url_validator'
  | 'property_scraper'
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
  const [isExpanded, setIsExpanded] = useState(true)

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
      case 'property_scraper':
        return 'Property Scraper'
      case 'response_formatter':
        return 'Formatter'
      case 'complete':
        return 'Complete'
    }
  }

  return (
    <div
      id={`agent-status-${phase}`}
      className="flex flex-col gap-3 rounded-2xl border border-zinc-200/65 bg-zinc-50/50 p-3.5 shadow-sm transition-all duration-300 dark:border-zinc-800/60 dark:bg-zinc-900/20 w-full max-w-[340px] sm:max-w-sm animate-fade-in"
    >
      <div className="flex items-center justify-between w-full gap-3">
        {/* Visual Indicator: Bouncing Pulse or Green Checkmark */}
        <div className="flex items-center gap-3 min-w-0">
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

        {/* Toggle Graph Button */}
        {!isComplete && (
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            id="toggle-workflow-graph"
            className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg border border-zinc-200 bg-white text-zinc-400 hover:text-zinc-600 hover:bg-zinc-50 transition-colors shadow-sm dark:border-zinc-800 dark:bg-zinc-950 dark:text-zinc-500 dark:hover:text-zinc-300 dark:hover:bg-zinc-900 cursor-pointer"
            title={isExpanded ? 'Hide execution workflow' : 'Show execution workflow'}
          >
            <svg
              className={`h-4 w-4 transform transition-transform duration-300 ${isExpanded ? 'rotate-180' : ''}`}
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"
              />
            </svg>
          </button>
        )}
      </div>

      {/* Expanded Workflow Graph Component */}
      {isExpanded && !isComplete && (
        <div className="mt-1 w-full border-t border-zinc-150/60 dark:border-zinc-800/80 pt-3">
          <WorkflowGraph currentPhase={phase} />
        </div>
      )}
    </div>
  )
}
