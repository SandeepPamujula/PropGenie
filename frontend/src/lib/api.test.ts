import { sendMessage, SessionExpiredError, RateLimitError } from './api'
import { resetSessionId } from './session'

jest.mock('./session', () => ({
  getSessionId: jest.fn(() => 'test-session-id'),
  resetSessionId: jest.fn(),
}))

describe('api', () => {
  const originalFetch = global.fetch

  beforeEach(() => {
    jest.clearAllMocks()
  })

  afterAll(() => {
    global.fetch = originalFetch
  })

  it('sends POST request to /api/chat with correct headers and body', async () => {
    const mockStream = {} as ReadableStream<Uint8Array>
    const mockFetch = jest.fn().mockResolvedValue({
      ok: true,
      status: 200,
      body: mockStream,
    })
    global.fetch = mockFetch

    const stream = await sendMessage('hello')

    expect(mockFetch).toHaveBeenCalledTimes(1)
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/chat'),
      expect.objectContaining({
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Accept: 'text/event-stream',
          'X-Session-ID': 'test-session-id',
        },
        body: JSON.stringify({ message: 'hello' }),
      }),
    )
    expect(stream).toBe(mockStream)
  })

  it('throws SessionExpiredError on 404 response', async () => {
    const mockFetch = jest.fn().mockResolvedValue({
      ok: false,
      status: 404,
      statusText: 'Not Found',
    })
    global.fetch = mockFetch

    await expect(sendMessage('hello')).rejects.toThrow(SessionExpiredError)
    expect(resetSessionId).toHaveBeenCalledTimes(1)
  })

  it('throws RateLimitError on 429 response', async () => {
    const mockFetch = jest.fn().mockResolvedValue({
      ok: false,
      status: 429,
      statusText: 'Too Many Requests',
    })
    global.fetch = mockFetch

    await expect(sendMessage('hello')).rejects.toThrow(RateLimitError)
  })

  it('throws standard Error on non-ok status code', async () => {
    const mockFetch = jest.fn().mockResolvedValue({
      ok: false,
      status: 500,
      statusText: 'Internal Server Error',
    })
    global.fetch = mockFetch

    await expect(sendMessage('hello')).rejects.toThrow(
      'Server returned an error: 500 Internal Server Error',
    )
  })

  it('throws Error if body stream is missing', async () => {
    const mockFetch = jest.fn().mockResolvedValue({
      ok: true,
      status: 200,
      body: null,
    })
    global.fetch = mockFetch

    await expect(sendMessage('hello')).rejects.toThrow('Response stream is empty')
  })
})
