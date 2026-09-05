import { describe, it, expect, vi, beforeEach } from 'vitest'

const mockGetCookie = vi.fn()
const mockSetCookie = vi.fn()
const mockDeleteCookie = vi.fn()
const mockGetMethod = vi.fn()
const mockGetHeader = vi.fn()
const mockSetResponseHeaders = vi.fn()
const mockSetResponseStatus = vi.fn()
const mockSend = vi.fn()
const mockReadBody = vi.fn()

vi.mock('h3', () => ({
  defineEventHandler: (fn: (event: unknown) => unknown) => fn,
  getCookie: (...args: unknown[]) => mockGetCookie(...args),
  setCookie: (...args: unknown[]) => mockSetCookie(...args),
  deleteCookie: (...args: unknown[]) => mockDeleteCookie(...args),
  getMethod: (...args: unknown[]) => mockGetMethod(...args),
  getHeader: (...args: unknown[]) => mockGetHeader(...args),
  setResponseHeaders: (...args: unknown[]) => mockSetResponseHeaders(...args),
  setResponseStatus: (...args: unknown[]) => mockSetResponseStatus(...args),
  send: (...args: unknown[]) => mockSend(...args),
  readBody: (...args: unknown[]) => mockReadBody(...args),
  createError: (opts: { statusCode: number; message: string; data?: unknown }) => {
    const err = new Error(opts.message) as Error & { statusCode: number; data?: unknown }
    err.statusCode = opts.statusCode
    err.data = opts.data
    return err
  },
}))

function makeEvent(path: string, url = `/api/proxy${path}`) {
  return {
    context: { params: { path: path.replace(/^\//, '').split('/') } },
    node: { req: { url } },
  } as never
}

const rawFetch = vi.fn()
const fetchRaw = vi.fn()

describe('server/api/proxy/[...path].ts', () => {
  beforeEach(() => {
    mockGetCookie.mockReset()
    mockSetCookie.mockReset()
    mockDeleteCookie.mockReset()
    mockGetMethod.mockReset()
    mockGetHeader.mockReset()
    mockSetResponseHeaders.mockReset()
    mockSetResponseStatus.mockReset()
    mockSend.mockReset()
    mockReadBody.mockReset()
    fetchRaw.mockReset()
    // The proxy handler calls $fetch.raw(), distinct from the plain $fetch used
    // by the auth routes — extend the global stub with a `.raw` method.
    vi.stubGlobal('$fetch', Object.assign(rawFetch, { raw: fetchRaw, create: vi.fn() }))
  })

  it('rejects a path outside the allowlist with 403 before contacting the backend', async () => {
    const { default: handler } = await import('../../../server/api/proxy/[...path]')
    mockGetMethod.mockReturnValue('GET')

    await expect(handler(makeEvent('/admin/secret'))).rejects.toMatchObject({ statusCode: 403 })
    expect(fetchRaw).not.toHaveBeenCalled()
  })

  it('rejects when no access token cookie is present', async () => {
    const { default: handler } = await import('../../../server/api/proxy/[...path]')
    mockGetMethod.mockReturnValue('GET')
    mockGetCookie.mockReturnValue(undefined)

    await expect(handler(makeEvent('/clients'))).rejects.toMatchObject({ statusCode: 401 })
    expect(mockDeleteCookie).toHaveBeenCalled()
  })

  it('forwards an allowlisted GET request with a Bearer token and returns the upstream body', async () => {
    const { default: handler } = await import('../../../server/api/proxy/[...path]')
    mockGetMethod.mockReturnValue('GET')
    mockGetCookie.mockImplementation((_e: unknown, name: string) => (name === 'at' ? 'valid-access-token' : undefined))
    mockGetHeader.mockReturnValue(undefined)
    fetchRaw.mockResolvedValueOnce({
      _data: [{ id: 'c1', name: 'Acme' }],
      status: 200,
      headers: new Map([['content-type', 'application/json']]),
    })

    const result = await handler(makeEvent('/clients'))

    expect(fetchRaw).toHaveBeenCalledWith(
      expect.stringContaining('/clients'),
      expect.objectContaining({
        headers: expect.objectContaining({ Authorization: 'Bearer valid-access-token' }),
      }),
    )
    expect(result).toEqual([{ id: 'c1', name: 'Acme' }])
    expect(mockSetResponseStatus).toHaveBeenCalledWith(expect.anything(), 200)
  })

  it('rotates the access token and retries exactly once on a 401 from upstream', async () => {
    const { default: handler } = await import('../../../server/api/proxy/[...path]')
    mockGetMethod.mockReturnValue('GET')
    mockGetCookie.mockImplementation((_e: unknown, name: string) => {
      if (name === 'at') return 'expired-access-token'
      if (name === 'rt') return 'valid-refresh-token'
      return undefined
    })
    mockGetHeader.mockReturnValue(undefined)

    fetchRaw
      .mockResolvedValueOnce({ _data: null, status: 401, headers: new Map() })
      .mockResolvedValueOnce({ _data: [{ id: 'c1' }], status: 200, headers: new Map() })
    rawFetch.mockResolvedValueOnce({ access_token: 'new-at', refresh_token: 'new-rt' })

    const result = await handler(makeEvent('/clients'))

    expect(rawFetch).toHaveBeenCalledWith(
      expect.stringContaining('/auth/refresh'),
      expect.objectContaining({ body: { refresh_token: 'valid-refresh-token' } }),
    )
    expect(mockSetCookie).toHaveBeenCalledWith(expect.anything(), 'at', 'new-at', expect.any(Object))
    expect(fetchRaw).toHaveBeenCalledTimes(2)
    expect(result).toEqual([{ id: 'c1' }])
  })

  it('clears cookies and rejects with 401 when the retry after refresh still fails', async () => {
    const { default: handler } = await import('../../../server/api/proxy/[...path]')
    mockGetMethod.mockReturnValue('GET')
    mockGetCookie.mockImplementation((_e: unknown, name: string) => {
      if (name === 'at') return 'expired-access-token'
      if (name === 'rt') return 'valid-refresh-token'
      return undefined
    })
    mockGetHeader.mockReturnValue(undefined)

    fetchRaw
      .mockResolvedValueOnce({ _data: null, status: 401, headers: new Map() })
      .mockResolvedValueOnce({ _data: null, status: 401, headers: new Map() })
    rawFetch.mockResolvedValueOnce({ access_token: 'new-at', refresh_token: 'new-rt' })

    await expect(handler(makeEvent('/clients'))).rejects.toMatchObject({ statusCode: 401 })
    expect(mockDeleteCookie).toHaveBeenCalled()
  })
})
