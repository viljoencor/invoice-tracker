import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mockToken, mockNavigateTo, mockFetchCreate, mockFetchClient } from '../../setup'
import { useApi } from '../../../composables/useApi'

describe('useApi', () => {
  let capturedOptions: any

  beforeEach(() => {
    mockFetchCreate.mockImplementation((opts: any) => {
      capturedOptions = opts
      return mockFetchClient
    })
  })

  it('passes apiBase as baseURL to $fetch.create', () => {
    useApi()
    expect(capturedOptions.baseURL).toBe('http://localhost:8000/api/v1')
  })

  it('returns get / post / patch / del / getArrayBuffer / getBlob helpers', () => {
    const api = useApi()
    expect(typeof api.get).toBe('function')
    expect(typeof api.post).toBe('function')
    expect(typeof api.patch).toBe('function')
    expect(typeof api.del).toBe('function')
    expect(typeof api.getArrayBuffer).toBe('function')
    expect(typeof api.getBlob).toBe('function')
  })

  it('api.get calls the fetch client with GET method', async () => {
    mockFetchClient.mockResolvedValue({ data: 'ok' })
    const api = useApi()
    await api.get('/invoices')
    expect(mockFetchClient).toHaveBeenCalledWith(
      '/invoices',
      expect.objectContaining({ method: 'GET' }),
    )
  })

  it('api.post calls the fetch client with POST method and body', async () => {
    mockFetchClient.mockResolvedValue({ id: 1 })
    const api = useApi()
    await api.post('/clients', { name: 'Acme' })
    expect(mockFetchClient).toHaveBeenCalledWith(
      '/clients',
      expect.objectContaining({ method: 'POST', body: { name: 'Acme' } }),
    )
  })

  it('sets Authorization header when token is set', () => {
    mockToken.value = 'jwt-abc123'
    useApi()

    const options = { headers: new Headers() }
    capturedOptions.onRequest({ options })

    expect((options.headers as Headers).get('Authorization')).toBe('Bearer jwt-abc123')
  })

  it('strips existing "Bearer " prefix before setting Authorization header', () => {
    mockToken.value = 'Bearer already-prefixed'
    useApi()

    const options = { headers: new Headers() }
    capturedOptions.onRequest({ options })

    expect((options.headers as Headers).get('Authorization')).toBe('Bearer already-prefixed')
  })

  it('omits Authorization header when no token', () => {
    mockToken.value = null
    useApi()

    const options = { headers: new Headers() }
    capturedOptions.onRequest({ options })

    expect((options.headers as Headers).has('Authorization')).toBe(false)
  })

  it('omits Authorization header when token is empty string', () => {
    mockToken.value = ''
    useApi()

    const options = { headers: new Headers() }
    capturedOptions.onRequest({ options })

    expect((options.headers as Headers).has('Authorization')).toBe(false)
  })

  it('clears token and navigates to /login on 401 response', async () => {
    mockToken.value = 'old-token'
    useApi()

    await capturedOptions.onResponseError({ response: { status: 401 } })

    expect(mockToken.value).toBeNull()
    expect(mockNavigateTo).toHaveBeenCalledWith('/login')
  })

  it('does not navigate on non-401 error responses', async () => {
    useApi()

    await capturedOptions.onResponseError({ response: { status: 500 } })

    expect(mockNavigateTo).not.toHaveBeenCalled()
  })

  it('prepends / to paths that do not start with /', async () => {
    mockFetchClient.mockResolvedValue({})
    const api = useApi()
    await api.get('invoices')
    expect(mockFetchClient).toHaveBeenCalledWith('/invoices', expect.anything())
  })
})
