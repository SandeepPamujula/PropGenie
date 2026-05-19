import type { SSEEventPayload } from '../types/sse'
import { consumeSSEStream } from './sse'

describe('sse', () => {
  // Helper to create a ReadableStream from string chunks
  function createMockStream(chunks: string[]): ReadableStream<Uint8Array> {
    const encoder = new TextEncoder()
    return new ReadableStream({
      start(controller) {
        for (const chunk of chunks) {
          controller.enqueue(encoder.encode(chunk))
        }
        controller.close()
      },
    })
  }

  it('correctly parses all 6 event types from an SSE stream', async () => {
    const ssePayloads: string[] = [
      'event: agent_status\ndata: {"type": "agent_status", "agent": "orchestrator", "message": "Understanding your search...", "timestamp": "2026-05-19T12:00:00Z"}\n\n',
      'event: clarification\ndata: {"type": "clarification", "message": "What is your budget?", "round": 1, "max_rounds": 3, "resolved_fields": {}, "missing_fields": ["budget"]}\n\n',
      'event: portal_card\ndata: {"portal": "nobroker", "label": "NoBroker Link", "summary": "2BHK Indiranagar", "url": "https://nobroker.in", "isPriority": true}\n\n',
      'event: search_meta\ndata: {"type": "search_meta", "portals_searched": 2, "portals_returned": 2, "portals_dropped": [], "clarification_rounds": 1, "defaults_applied": []}\n\n',
      'event: error\ndata: {"type": "error", "message": "An execution error occurred", "retryable": true}\n\n',
      'event: done\ndata: {"type": "done", "session_id": "test-session", "search_count_today": 3, "search_limit": 10}\n\n',
    ]

    const stream = createMockStream(ssePayloads)
    const events: SSEEventPayload[] = []
    const onEvent = jest.fn((e: SSEEventPayload) => {
      events.push(e)
    })

    await consumeSSEStream(stream, onEvent)

    expect(onEvent).toHaveBeenCalledTimes(6)

    expect(events[0]).toEqual({
      event: 'agent_status',
      data: {
        type: 'agent_status',
        agent: 'orchestrator',
        message: 'Understanding your search...',
        timestamp: '2026-05-19T12:00:00Z',
      },
    })

    expect(events[1]).toEqual({
      event: 'clarification',
      data: {
        type: 'clarification',
        message: 'What is your budget?',
        round: 1,
        max_rounds: 3,
        resolved_fields: {},
        missing_fields: ['budget'],
      },
    })

    expect(events[2]).toEqual({
      event: 'portal_card',
      data: {
        portal: 'nobroker',
        label: 'NoBroker Link',
        summary: '2BHK Indiranagar',
        url: 'https://nobroker.in',
        isPriority: true,
      },
    })

    expect(events[3]).toEqual({
      event: 'search_meta',
      data: {
        type: 'search_meta',
        portals_searched: 2,
        portals_returned: 2,
        portals_dropped: [],
        clarification_rounds: 1,
        defaults_applied: [],
      },
    })

    expect(events[4]).toEqual({
      event: 'error',
      data: {
        type: 'error',
        message: 'An execution error occurred',
        retryable: true,
      },
    })

    expect(events[5]).toEqual({
      event: 'done',
      data: {
        type: 'done',
        session_id: 'test-session',
        search_count_today: 3,
        search_limit: 10,
      },
    })
  })

  it('handles events sent in multiple chunks split across line breaks', async () => {
    const chunks = [
      'event: agent',
      '_status\ndata: {"type": "agent_status", "agent": "orchestrator", "message": "Under',
      'standing...", "timestamp": "now"}\n\n',
    ]

    const stream = createMockStream(chunks)
    const onEvent = jest.fn()

    await consumeSSEStream(stream, onEvent)

    expect(onEvent).toHaveBeenCalledTimes(1)
    expect(onEvent).toHaveBeenCalledWith({
      event: 'agent_status',
      data: {
        type: 'agent_status',
        agent: 'orchestrator',
        message: 'Understanding...',
        timestamp: 'now',
      },
    })
  })
})
