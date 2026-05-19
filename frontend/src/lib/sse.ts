import type { SSEEventPayload } from '../types/sse'

export type SSEHandler = (payload: SSEEventPayload) => void

/**
 * Consumes a fetch response ReadableStream and parses it into Server-Sent Events (SSE).
 *
 * @param stream The response body ReadableStream.
 * @param onEvent Callback triggered for each parsed SSE event.
 */
export async function consumeSSEStream(
  stream: ReadableStream<Uint8Array>,
  onEvent: SSEHandler,
): Promise<void> {
  const reader = stream.getReader()
  const decoder = new TextDecoder('utf-8')
  let buffer = ''

  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) {
        break
      }

      // Decode the new chunk and append it to our buffer
      buffer += decoder.decode(value, { stream: true })

      // Server-sent events are separated by double newlines (\n\n or \r\n\r\n)
      const parts = buffer.split(/\r?\n\r?\n/)
      
      // The last part might be incomplete, save it back to the buffer
      buffer = parts.pop() || ''

      for (const part of parts) {
        if (!part.trim()) {
          continue
        }

        let eventType = 'message'
        let dataContent = ''

        // Split by lines to parse event type and data
        const lines = part.split(/\r?\n/)
        for (const line of lines) {
          if (line.startsWith('event:')) {
            eventType = line.slice(6).trim()
          } else if (line.startsWith('data:')) {
            // Append data in case it spans multiple lines (though standard JSON data is single-line here)
            dataContent += (dataContent ? '\n' : '') + line.slice(5).trim()
          }
        }

        if (dataContent) {
          try {
            const parsedData = JSON.parse(dataContent) as Record<string, unknown>
            
            // Format and cast to typed SSEEventPayload
            const payload = {
              event: eventType,
              data: parsedData,
            } as unknown as SSEEventPayload
            
            onEvent(payload)
          } catch (e) {
            console.error('[SSE Parser] Failed to parse event JSON data:', dataContent, e)
          }
        }
      }
    }
  } catch (error) {
    console.error('[SSE Parser] Error reading stream:', error)
    throw error;
  } finally {
    reader.releaseLock()
  }
}
