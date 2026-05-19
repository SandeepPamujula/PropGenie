import { getSessionId, resetSessionId } from './session'

describe('session', () => {
  const mockUUID = '12345678-1234-4321-abcd-123456789abc'

  beforeAll(() => {
    // Mock crypto.randomUUID for environments where it is not available (like older JSDOM)
    if (typeof crypto === 'undefined' || !crypto.randomUUID) {
      Object.defineProperty(global, 'crypto', {
        value: {
          randomUUID: () => mockUUID,
        },
        writable: true,
      })
    } else {
      jest.spyOn(crypto, 'randomUUID').mockImplementation(() => mockUUID)
    }
  })

  beforeEach(() => {
    sessionStorage.clear()
    jest.clearAllMocks()
  })

  it('generates a new session ID if one does not exist', () => {
    const id = getSessionId()
    expect(id).toBe(mockUUID)
    expect(sessionStorage.getItem('propgenie_session_id')).toBe(mockUUID)
  })

  it('persists session ID and returns the same ID on subsequent calls', () => {
    const id1 = getSessionId()
    const id2 = getSessionId()
    expect(id1).toBe(id2)
    expect(sessionStorage.getItem('propgenie_session_id')).toBe(id1)
  })

  it('forces generating a new session ID when resetSessionId is called', () => {
    const id1 = getSessionId()
    expect(id1).toBe(mockUUID)

    let calls = 0
    jest.spyOn(crypto, 'randomUUID').mockImplementation(() => {
      calls++
      return `new-uuid-${calls}`
    })

    const id2 = resetSessionId()
    expect(id2).toBe('new-uuid-1')
    expect(sessionStorage.getItem('propgenie_session_id')).toBe('new-uuid-1')
    expect(id1).not.toBe(id2)
  })
})
