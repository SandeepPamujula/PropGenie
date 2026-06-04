import { getSessionId, resetSessionId } from './session'

const isDev = process.env.NODE_ENV === 'development'
export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || (isDev ? 'http://localhost:8000' : '')

export class SessionExpiredError extends Error {
  constructor(message = 'Session has expired') {
    super(message)
    this.name = 'SessionExpiredError'
  }
}

export class RateLimitError extends Error {
  constructor(message = 'Rate limit reached') {
    super(message)
    this.name = 'RateLimitError'
  }
}

/**
 * Sends a message to the PropGenie backend chat endpoint.
 *
 * @param message The user message query to submit.
 * @returns A Promise resolving to a ReadableStream for SSE streaming consumption.
 * @throws SessionExpiredError if the session is invalid or expired.
 * @throws RateLimitError if the user's daily search limit is exceeded.
 */
export async function sendMessage(message: string): Promise<ReadableStream<Uint8Array>> {
  const sessionId = getSessionId()
  const bodyString = JSON.stringify({ message })

  // Compute SHA-256 hash of body for AWS SigV4 / CloudFront OAC verification on POST requests
  let contentSha256 = 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855' // empty body SHA-256
  if (bodyString) {
    const encoder = new TextEncoder()
    const data = encoder.encode(bodyString)
    const hashBuffer = await crypto.subtle.digest('SHA-256', data)
    const hashArray = Array.from(new Uint8Array(hashBuffer))
    contentSha256 = hashArray.map((b) => b.toString(16).padStart(2, '0')).join('')
  }

  const response = await fetch(`${API_BASE_URL}/api/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'text/event-stream',
      'X-Session-ID': sessionId,
      'x-amz-content-sha256': contentSha256,
    },
    body: bodyString,
  })

  if (response.status === 404) {
    // If the session has expired or is invalid, reset and throw
    resetSessionId()
    throw new SessionExpiredError('Your search session has expired. Starting a new session.')
  }

  if (response.status === 429) {
    throw new RateLimitError(
      'You have reached your daily search limit of 10. Please try again tomorrow.',
    )
  }

  if (!response.ok) {
    throw new Error(`Server returned an error: ${response.status} ${response.statusText}`)
  }

  if (!response.body) {
    throw new Error('Response stream is empty')
  }

  return response.body
}
