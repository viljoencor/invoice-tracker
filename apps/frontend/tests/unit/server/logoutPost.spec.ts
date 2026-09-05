import { describe, it, expect, vi, beforeEach } from 'vitest'
import { $fetchMock } from '../../setup'

const mockGetCookie = vi.fn()
const mockDeleteCookie = vi.fn()

vi.mock('h3', () => ({
  defineEventHandler: (fn: (event: unknown) => unknown) => fn,
  getCookie: (...args: unknown[]) => mockGetCookie(...args),
  deleteCookie: (...args: unknown[]) => mockDeleteCookie(...args),
  setCookie: vi.fn(),
  readBody: vi.fn(),
  createError: (opts: { statusCode: number; message: string }) => {
    const err = new Error(opts.message) as Error & { statusCode: number }
    err.statusCode = opts.statusCode
    return err
  },
}))

const fakeEvent = {} as never

describe('server/api/auth/logout.post.ts', () => {
  beforeEach(() => {
    mockGetCookie.mockReset()
    mockDeleteCookie.mockReset()
  })

  it('revokes the refresh token on the backend and always clears local cookies', async () => {
    const { default: handler } = await import('../../../server/api/auth/logout.post')
    mockGetCookie.mockReturnValue('raw-refresh-token')
    $fetchMock.mockResolvedValueOnce({ ok: true })

    const result = await handler(fakeEvent)

    expect($fetchMock).toHaveBeenCalledWith(
      expect.stringContaining('/auth/logout'),
      expect.objectContaining({ method: 'POST', body: { refresh_token: 'raw-refresh-token' } }),
    )
    expect(mockDeleteCookie).toHaveBeenCalledWith(fakeEvent, 'at', expect.any(Object))
    expect(mockDeleteCookie).toHaveBeenCalledWith(fakeEvent, 'rt', expect.any(Object))
    expect(mockDeleteCookie).toHaveBeenCalledWith(fakeEvent, 'session', expect.any(Object))
    expect(result).toEqual({ ok: true })
  })

  it('still clears local cookies when the backend revocation call fails', async () => {
    const { default: handler } = await import('../../../server/api/auth/logout.post')
    mockGetCookie.mockReturnValue('raw-refresh-token')
    $fetchMock.mockRejectedValueOnce(new Error('backend unreachable'))

    const result = await handler(fakeEvent)

    expect(mockDeleteCookie).toHaveBeenCalledWith(fakeEvent, 'at', expect.any(Object))
    expect(mockDeleteCookie).toHaveBeenCalledWith(fakeEvent, 'rt', expect.any(Object))
    expect(result).toEqual({ ok: true })
  })

  it('clears cookies without calling the backend when no refresh token cookie exists', async () => {
    const { default: handler } = await import('../../../server/api/auth/logout.post')
    mockGetCookie.mockReturnValue(undefined)

    await handler(fakeEvent)

    expect($fetchMock).not.toHaveBeenCalled()
    expect(mockDeleteCookie).toHaveBeenCalledWith(fakeEvent, 'at', expect.any(Object))
  })
})
