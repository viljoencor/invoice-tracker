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

describe('server/api/auth/register.post.ts', () => {
  beforeEach(() => {
    mockReadBody.mockReset()
    mockSetCookie.mockReset()
  })

  it('rejects a request missing name, email, or password with 400', async () => {
    const { default: handler } = await import('../../../server/api/auth/register.post')
    mockReadBody.mockResolvedValue({ name: '', email: '', password: '' })

    await expect(handler(fakeEvent)).rejects.toMatchObject({ statusCode: 400 })
    expect($fetchMock).not.toHaveBeenCalled()
  })

  it('forwards valid registration details to the backend and sets httpOnly cookies on success', async () => {
    const { default: handler } = await import('../../../server/api/auth/register.post')
    mockReadBody.mockResolvedValue({ name: 'Jane Doe', email: 'jane@example.com', password: 'hunter22' })
    $fetchMock.mockResolvedValueOnce({ access_token: 'at-123', refresh_token: 'rt-456' })

    const result = await handler(fakeEvent)

    expect($fetchMock).toHaveBeenCalledWith(
      expect.stringContaining('/auth/register'),
      expect.objectContaining({
        method: 'POST',
        body: { name: 'Jane Doe', email: 'jane@example.com', password: 'hunter22' },
      }),
    )
    expect(mockSetCookie).toHaveBeenCalledWith(fakeEvent, 'at', 'at-123', expect.any(Object))
    expect(mockSetCookie).toHaveBeenCalledWith(fakeEvent, 'rt', 'rt-456', expect.any(Object))
    expect(mockSetCookie).toHaveBeenCalledWith(fakeEvent, 'session', '1', expect.any(Object))
    expect(result).toEqual({ ok: true })
    expect(JSON.stringify(result)).not.toContain('at-123')
  })

  it('surfaces the backend error (e.g. duplicate email) instead of a generic message', async () => {
    const { default: handler } = await import('../../../server/api/auth/register.post')
    mockReadBody.mockResolvedValue({ name: 'Jane Doe', email: 'jane@example.com', password: 'hunter22' })
    $fetchMock.mockRejectedValueOnce({ status: 400, data: { detail: 'Email already registered' } })

    await expect(handler(fakeEvent)).rejects.toMatchObject({
      statusCode: 400,
      message: 'Email already registered',
    })
    expect(mockSetCookie).not.toHaveBeenCalled()
  })
})
