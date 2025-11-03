// apps/frontend/composables/useApi.ts
export function useApi() {
  const { public: { apiBase } } = useRuntimeConfig()

  const configured = (apiBase || '').trim()
  const baseCandidate = configured !== '' ? configured : 'http://localhost:8000/api/v1'
  let base = baseCandidate.replace(/\/+$/, '')
  if (!/\/api\/v\d+$/.test(base)) base = `${base}/api/v1`

  if (process.dev) {
    // eslint-disable-next-line no-console
    console.log('[useApi] baseURL =', base)
  }

  const tokenCookie = useCookie<string | null>('token', { sameSite: 'lax' })

  // Shared client: injects Authorization, same as before
  const client = $fetch.create({
    baseURL: base,
    credentials: 'omit',
    onRequest({ options }) {
      const headers = new Headers(options.headers as any)
      if (!headers.has('Content-Type')) headers.set('Content-Type', 'application/json')

      const raw = (tokenCookie.value ?? '').trim()
      const jwt = raw.replace(/^bearer\s+/i, '').trim()
      if (jwt) headers.set('Authorization', `Bearer ${jwt}`)

      options.headers = headers
    },
    onResponseError({ response }) {
      if (response.status === 401) {
        tokenCookie.value = null
        return navigateTo('/login')
      }
    },
  })

  const join = (p: string) => (p.startsWith('/') ? p : `/${p}`)

  return {
    // JSON helpers
    get:   (path: string, opts?: any) => client(join(path), { method: 'GET', ...opts }),
    post:  (path: string, body?: any, opts?: any) =>
      client(join(path), { method: 'POST', body, ...opts }),
    patch: (path: string, body?: any, opts?: any) =>
      client(join(path), { method: 'PATCH', body, ...opts }),
    del:   (path: string, opts?: any) => client(join(path), { method: 'DELETE', ...opts }),

    // NEW: binary helpers (still send Authorization)
    getArrayBuffer: (path: string, opts?: any) =>
      client(join(path), { method: 'GET', responseType: 'arrayBuffer', ...opts }),
    getBlob: (path: string, opts?: any) =>
      client(join(path), { method: 'GET', responseType: 'blob', ...opts }),
  }
}
