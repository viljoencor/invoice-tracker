// apps/frontend/composables/useApi.ts
// All API traffic goes through the Nitro BFF proxy at /api/proxy/*.
// httpOnly cookies carry the tokens — no client-side token management here.
export function useApi() {
  // Step 1: Create base ofetch client pointing at BFF proxy with cookie credentials.
  const client = $fetch.create({
    baseURL: '/api/proxy',
    credentials: 'include', // send httpOnly session cookies
    onResponseError({ response }) {
      // Step 2: Redirect to /login when BFF exhausts both access and refresh tokens.
      if (response.status === 401) void navigateTo('/login')
    },
  })

  // Step 3: Normalise path to always have a leading slash.
  const join = (p: string) => (p.startsWith('/') ? p : `/${p}`)

  return {
    // GET request forwarded through BFF proxy.
    get:   <T = unknown>(path: string, opts?: any) => client<T>(join(path), { method: 'GET', ...opts }),
    // POST request; body serialised to JSON by ofetch.
    post:  <T = unknown>(path: string, body?: any, opts?: any) => client<T>(join(path), { method: 'POST', body, ...opts }),
    // PATCH request for partial updates.
    patch: <T = unknown>(path: string, body?: any, opts?: any) => client<T>(join(path), { method: 'PATCH', body, ...opts }),
    // DELETE request scoped by path.
    del:   <T = unknown>(path: string, opts?: any) => client<T>(join(path), { method: 'DELETE', ...opts }),

    // Binary helpers — used for PDF download.
    getArrayBuffer: (path: string, opts?: any) =>
      client<ArrayBuffer>(join(path), { method: 'GET', responseType: 'arrayBuffer', ...opts }),
    getBlob: (path: string, opts?: any) =>
      client<Blob>(join(path), { method: 'GET', responseType: 'blob', ...opts }),
  }
}
