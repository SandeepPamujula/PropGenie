import type { Portal } from './domain'

export interface AgentStatusEvent {
  type: 'agent_status'
  agent: 'orchestrator' | 'clarification' | 'query_builder' | 'url_validator' | 'response_formatter'
  message: string
  timestamp: string
}

export interface ClarificationEvent {
  type: 'clarification'
  message: string
  round: number
  max_rounds: number
  resolved_fields: Record<string, unknown>
  missing_fields: string[]
}

export interface PortalCardEvent {
  portal: Portal
  label?: string
  summary: string
  url: string
  isPriority?: boolean
  priority?: boolean
  notes?: string
}

export interface SearchMetaEvent {
  type: 'search_meta'
  portals_searched: number
  portals_returned: number
  portals_dropped: string[]
  clarification_rounds: number
  defaults_applied: string[]
}

export interface ErrorEvent {
  type: 'error'
  message: string
  retryable: boolean
}

export interface DoneEvent {
  type: 'done'
  session_id: string
  search_count_today: number
  search_limit: number
}

export type SSEEventPayload =
  | { event: 'agent_status'; data: AgentStatusEvent }
  | { event: 'clarification'; data: ClarificationEvent }
  | { event: 'portal_card'; data: PortalCardEvent }
  | { event: 'search_meta'; data: SearchMetaEvent }
  | { event: 'error'; data: ErrorEvent }
  | { event: 'done'; data: DoneEvent }
