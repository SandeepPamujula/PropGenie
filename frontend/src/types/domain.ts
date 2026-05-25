export type Intent = 'buy' | 'rent' | 'ambiguous'

export type PropertyType = 'plot' | 'apartment' | 'villa' | 'house'

export type Portal = 'nobroker' | '99acres' | 'magicbricks' | 'housing' | 'squareyards'

export interface PortalResult {
  portal: Portal
  label: string
  summary: string
  url: string
  isPriority: boolean
  notes?: string
}

export interface SearchMeta {
  portalsSearched: number
  portalsReturned: number
  portalsDropped: string[]
  clarificationRounds: number
  defaultsApplied: string[]
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: string
  type?: 'text' | 'clarification' | 'portal_cards' | 'error'
  clarificationRound?: number
  clarificationMaxRounds?: number
  resolvedFields?: Record<string, unknown>
  missingFields?: string[]
  portalResults?: PortalResult[]
  searchMeta?: SearchMeta
}

export interface SessionContext {
  sessionId: string
  intent?: Intent
  city?: string
  locationAnchor?: string
  propertyType?: PropertyType
  bhk?: number
  budgetMin?: number
  budgetMax?: number
  radiusKm: number
  clarificationRound: number
}
