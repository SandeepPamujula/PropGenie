const SESSION_KEY = 'propgenie_session_id'

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
    sessionId = crypto.randomUUID()
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

  const newSessionId = crypto.randomUUID()
  sessionStorage.setItem(SESSION_KEY, newSessionId)
  return newSessionId
}
