import { describe, it, expect, vi, beforeEach } from 'vitest'
import { $fetchMock } from '../../setup'

const mockGetCookie = vi.fn()
const mockSetCookie = vi.fn()
const mockDeleteCookie = vi.fn()

vi.mock('h3', () => ({
  defineEventHandler: (fn: (event: unknown) => unknown) => fn,
  getCookie: (...args: unknown[]) => mockGetCookie(...args),
  setCookie: (...args: unknown[]) => mockSetCookie(...args),
  deleteCookie: (...args: unknown[]) => mockDeleteCookie(...args),
  readBody: vi.fn(),
  createError: (opts: { statusCode: number; message: string }) => {
    const err = new Error(opts.message) as Error & { statusCode: number }
    err.statusCode = opts.statusCode
    return err
  },
}))

const fakeEvent = {} as never

describe('server/api/auth/refresh.post.ts', () => {
  beforeEach(() => {
    mockGetCookie.mockReset()
    mockSetCookie.mockReset()
    mockDeleteCookie.mockReset()
  })

  it('rejects with 401 and clears cookies when no refresh token cookie is present', async () => {
    const { default: handler } = await import('../../../server/api/auth/refresh.post')
    mockGetCookie.mockReturnValue(undefined)

    await expect(handler(fakeEvent)).rejects.toMatchObject({ statusCode: 401 })
    expect(mockDeleteCookie).toHaveBeenCalledWith(fakeEvent, 'at', expect.any(Object))
    expect($fetchMock).not.toHaveBeenCalled()
  })

  it('rotates both tokens on a successful refresh', async () => {
    const { default: handler } = await import('../../../server/api/auth/refresh.post')
    mockGetCookie.mockReturnValue('old-refresh-token')
    $fetchMock.mockResolvedValueOnce({ access_token: 'new-at', refresh_token: 'new-rt' })

    const result = await handler(fakeEvent)

    expect($fetchMock).toHaveBeenCalledWith(
      expect.stringContaining('/auth/refresh'),
      expect.objectContaining({ method: 'POST', body: { refresh_token: 'old-refresh-token' } }),
    )
    expect(mockSetCookie).toHaveBeenCalledWith(fakeEvent, 'at', 'new-at', expect.any(Object))
    expect(mockSetCookie).toHaveBeenCalledWith(fakeEvent, 'rt', 'new-rt', expect.any(Object))
    expect(result).toEqual({ ok: true })
  })

  it('clears cookies and rejects with 401 when the backend rejects the refresh token', async () => {
    const { default: handler } = await import('../../../server/api/auth/refresh.post')
    mockGetCookie.mockReturnValue('expired-or-revoked-token')
    $fetchMock.mockRejectedValueOnce({ status: 401 })

    await expect(handler(fakeEvent)).rejects.toMatchObject({ statusCode: 401 })
    expect(mockDeleteCookie).toHaveBeenCalledWith(fakeEvent, 'rt', expect.any(Object))
    expect(mockSetCookie).not.toHaveBeenCalled()
  })
})
