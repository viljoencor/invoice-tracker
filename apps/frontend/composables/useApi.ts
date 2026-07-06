// apps/frontend/composables/useApi.ts
// All API traffic goes through the Nitro BFF proxy at /api/proxy/*.
// httpOnly cookies carry the tokens — no client-side token management here.
export function useApi() {
  const client = $fetch.create({
    baseURL: '/api/proxy',
    credentials: 'include', // send httpOnly session cookies
    onResponseError({ response }) {
      // Proxy returns 401 when both access and refresh tokens are exhausted
      if (response.status === 401) void navigateTo('/login')
    },
  })

  const join = (p: string) => (p.startsWith('/') ? p : `/${p}`)

  return {
    get:   <T = unknown>(path: string, opts?: any) => client<T>(join(path), { method: 'GET', ...opts }),
    post:  <T = unknown>(path: string, body?: any, opts?: any) => client<T>(join(path), { method: 'POST', body, ...opts }),
    patch: <T = unknown>(path: string, body?: any, opts?: any) => client<T>(join(path), { method: 'PATCH', body, ...opts }),
    del:   <T = unknown>(path: string, opts?: any) => client<T>(join(path), { method: 'DELETE', ...opts }),

    // Binary helpers
    getArrayBuffer: (path: string, opts?: any) =>
      client<ArrayBuffer>(join(path), { method: 'GET', responseType: 'arrayBuffer', ...opts }),
    getBlob: (path: string, opts?: any) =>
      client<Blob>(join(path), { method: 'GET', responseType: 'blob', ...opts }),
  }
}
