const SESSION_KEY = 'propgenie_session_id'

/**
 * Helper to generate a UUID v4.
 * Uses crypto.randomUUID() if available, otherwise falls back to a pseudo-random generator
 * for non-secure contexts (HTTP, IP address access in local network, etc.).
 */
function generateUUID(): string {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID()
  }
  // Mathematical fallback for UUID v4 compliance
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0
    const v = c === 'x' ? r : (r & 0x3) | 0x8
    return v.toString(16)
  })
}

/**
 * Returns the current session ID from sessionStorage.
 * If no session ID exists, it generates a new UUID v4 and stores it.
 */
export function getSessionId(): string {
  if (typeof window === 'undefined') {
    return ''
  }

  let sessionId = sessionStorage.getItem(SESSION_KEY)
  if (!sessionId) {
    sessionId = generateUUID()
    sessionStorage.setItem(SESSION_KEY, sessionId)
  }

  return sessionId
}

/**
 * Force-generates a new session ID, stores it in sessionStorage, and returns it.
 * This is used for session expiry scenarios.
 */
export function resetSessionId(): string {
  if (typeof window === 'undefined') {
    return ''
  }

  const newSessionId = generateUUID()
  sessionStorage.setItem(SESSION_KEY, newSessionId)
  return newSessionId
}
