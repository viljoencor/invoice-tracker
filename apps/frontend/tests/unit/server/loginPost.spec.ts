import { describe, it, expect, vi, beforeEach } from 'vitest'
import { $fetchMock } from '../../setup'

const mockReadBody = vi.fn()
const mockSetCookie = vi.fn()

vi.mock('h3', () => ({
  defineEventHandler: (fn: (event: unknown) => unknown) => fn,
  readBody: (...args: unknown[]) => mockReadBody(...args),
  setCookie: (...args: unknown[]) => mockSetCookie(...args),
  getCookie: vi.fn(),
  deleteCookie: vi.fn(),
  createError: (opts: { statusCode: number; message: string }) => {
    const err = new Error(opts.message) as Error & { statusCode: number }
    err.statusCode = opts.statusCode
    return err
  },
}))

const fakeEvent = {} as never

describe('server/api/auth/login.post.ts', () => {
  beforeEach(() => {
    mockReadBody.mockReset()
    mockSetCookie.mockReset()
  })

  it('rejects a request missing email or password with 400', async () => {
    const { default: handler } = await import('../../../server/api/auth/login.post')
    mockReadBody.mockResolvedValue({ email: '', password: '' })

    await expect(handler(fakeEvent)).rejects.toMatchObject({ statusCode: 400 })
  })

  it('forwards valid credentials to the backend and sets httpOnly cookies on success', async () => {
    const { default: handler } = await import('../../../server/api/auth/login.post')
    mockReadBody.mockResolvedValue({ email: 'admin@example.com', password: 'admin123' })
    $fetchMock.mockResolvedValueOnce({ access_token: 'at-123', refresh_token: 'rt-456' })

    const result = await handler(fakeEvent)

    expect($fetchMock).toHaveBeenCalledWith(
      expect.stringContaining('/auth/login'),
      expect.objectContaining({
        method: 'POST',
        body: { email: 'admin@example.com', password: 'admin123' },
      }),
    )
    // Access token, refresh token, and session-indicator cookies are all set.
    expect(mockSetCookie).toHaveBeenCalledWith(fakeEvent, 'at', 'at-123', expect.any(Object))
    expect(mockSetCookie).toHaveBeenCalledWith(fakeEvent, 'rt', 'rt-456', expect.any(Object))
    expect(mockSetCookie).toHaveBeenCalledWith(fakeEvent, 'session', '1', expect.any(Object))
    // Deliberately never returns the raw tokens in the response body.
    expect(result).toEqual({ ok: true })
    expect(JSON.stringify(result)).not.toContain('at-123')
    expect(JSON.stringify(result)).not.toContain('rt-456')
  })

  it('surfaces a 401 with a generic message when the backend rejects the credentials', async () => {
    const { default: handler } = await import('../../../server/api/auth/login.post')
    mockReadBody.mockResolvedValue({ email: 'admin@example.com', password: 'wrong' })
    $fetchMock.mockRejectedValueOnce({ status: 401, data: { detail: 'Invalid credentials' } })

    await expect(handler(fakeEvent)).rejects.toMatchObject({ statusCode: 401 })
    expect(mockSetCookie).not.toHaveBeenCalled()
  })
})
