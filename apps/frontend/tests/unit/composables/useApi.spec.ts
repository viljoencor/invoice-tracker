import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mockNavigateTo, mockFetchCreate, mockFetchClient } from '../../setup'
import { useApi } from '../../../composables/useApi'

describe('useApi', () => {
  let capturedOptions: any

  beforeEach(() => {
    mockFetchCreate.mockImplementation((opts: any) => {
      capturedOptions = opts
      return mockFetchClient
    })
  })

  it('uses /api/proxy as baseURL (same-origin BFF)', () => {
    useApi()
    expect(capturedOptions.baseURL).toBe('/api/proxy')
  })

  it('sends credentials:include so httpOnly cookies are forwarded', () => {
    useApi()
    expect(capturedOptions.credentials).toBe('include')
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

  it('navigates to /login on 401 response from proxy', async () => {
    useApi()
    await capturedOptions.onResponseError({ response: { status: 401 } })
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
