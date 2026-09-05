import {
  defineEventHandler,
  getCookie,
  getMethod,
  getHeader,
  setResponseHeaders,
  setResponseStatus,
  createError,
  send,
} from 'h3'
import { setAuthCookies, clearAuthCookies } from '../../utils/cookies'
import { getBackendBase } from '../../utils/backend'

/** Only these path prefixes are permitted through the proxy (no open proxy). */
export const ALLOWED_PREFIXES = [
  '/clients',
  '/invoices',
  '/payments',
  '/dash',
  '/auth/me',
]

/** Returns true when the upstream path is on the explicit allow-list (no open proxy).
 * Exported (like checkOriginMatchesHost) so this security-critical check can be
 * unit-tested directly without constructing a full H3 event. */
export function isAllowedPath(path: string): boolean {
  // Step 1: Match exact prefix, prefix + slash, or prefix + query string.
  return ALLOWED_PREFIXES.some(
    (prefix) =>
      path === prefix ||
      path.startsWith(prefix + '/') ||
      path.startsWith(prefix + '?'),
  )
}

/** Headers from the browser request that are safe to forward upstream. */
const FORWARD_REQUEST_HEADERS = ['idempotency-key', 'x-request-id']

/** Headers from the upstream response that are safe to return to the browser. */
const FORWARD_RESPONSE_HEADERS = [
  'content-type',
  'content-disposition',
  'x-trace-id',
]

type UpstreamResponse = { _data: unknown; status: number; headers: Headers }

/**
 * Forward a single request to the FastAPI backend.
 * Step 1: Build auth + extra headers; 
 * Step 2: Attach body for non-GET; 
 * Step 3: Set arrayBuffer mode for PDF;
 * Step 4: Execute $fetch.raw; 
 * Step 5: Return status, headers, and data.
 */
type HttpMethod = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE' | 'HEAD' | 'OPTIONS' | 'CONNECT' | 'TRACE'

async function callUpstream(
  method: HttpMethod,
  url: string,
  accessToken: string,
  body: unknown,
  extraHeaders: Record<string, string>,
  isPdf: boolean,
): Promise<UpstreamResponse> {
  const headers: Record<string, string> = {
    Authorization: `Bearer ${accessToken}`,
    ...extraHeaders,
  }

  const fetchOpts: {
    method: HttpMethod
    headers: Record<string, string>
    signal: AbortSignal
    ignoreResponseError: boolean
    body?: Record<string, any> | BodyInit | null
    responseType?: 'arrayBuffer'
  } = {
    method,
    headers,
    signal: AbortSignal.timeout(30_000),
    // Prevent ofetch from throwing on HTTP errors so we can inspect the status
    ignoreResponseError: true,
  }

  if (body !== undefined && !['GET', 'HEAD', 'DELETE'].includes(method.toUpperCase())) {
    fetchOpts.body = body as Record<string, any> | BodyInit | null
    headers['Content-Type'] = 'application/json'
  }

  if (isPdf) {
    fetchOpts.responseType = 'arrayBuffer'
  }

  const response = await $fetch.raw<unknown>(url, fetchOpts)
  return { _data: response._data, status: response.status, headers: response.headers }
}

export default defineEventHandler(async (event) => {
  // ── 1. Resolve the upstream path ──────────────────────────────────────────
  const rawPath = event.context.params?.path
  const pathSegments = Array.isArray(rawPath) ? rawPath.join('/') : (rawPath ?? '')
  const upstreamPath = `/${pathSegments}`

  if (!isAllowedPath(upstreamPath)) {
    throw createError({ statusCode: 403, message: `Path not permitted: ${upstreamPath}` })
  }

  // Preserve the query string from the original request
  const reqUrl: string = event.node.req.url ?? ''
  const qIdx = reqUrl.indexOf('?')
  const qs = qIdx >= 0 ? reqUrl.slice(qIdx) : ''

  const base = getBackendBase()
  const upstreamUrl = `${base}${upstreamPath}${qs}`

  // ── 2. Read the access token from the httpOnly cookie ─────────────────────
  let accessToken = getCookie(event, 'at')
  if (!accessToken) {
    clearAuthCookies(event)
    throw createError({ statusCode: 401, message: 'Not authenticated' })
  }

  const method = getMethod(event) as HttpMethod
  const isPdf = upstreamPath.endsWith('/pdf')

  // ── 3. Collect safe headers to forward; generate trace ID if absent ──────
  const extraHeaders: Record<string, string> = {}
  for (const h of FORWARD_REQUEST_HEADERS) {
    const val = getHeader(event, h)
    if (val) extraHeaders[h] = val
  }
  // Forward browser trace ID or generate one so every upstream call is correlated
  extraHeaders['x-trace-id'] = getHeader(event, 'x-trace-id') || crypto.randomUUID()

  // ── 4. Read body for state-changing methods ───────────────────────────────
  let body: unknown
  if (!['GET', 'HEAD'].includes(method.toUpperCase())) {
    try {
      const { readBody } = await import('h3')
      body = await readBody(event)
    } catch {
      body = undefined
    }
  }

  // ── 5. First attempt ──────────────────────────────────────────────────────
  let res = await callUpstream(method, upstreamUrl, accessToken, body, extraHeaders, isPdf)

  // ── 6. On 401, attempt token refresh then retry once ─────────────────────
  if (res.status === 401) {
    const rt = getCookie(event, 'rt')
    if (!rt) {
      clearAuthCookies(event)
      throw createError({ statusCode: 401, message: 'Session expired' })
    }

    let refreshData: { access_token: string; refresh_token: string }
    try {
      refreshData = await $fetch<{ access_token: string; refresh_token: string }>(
        `${base}/auth/refresh`,
        {
          method: 'POST',
          body: { refresh_token: rt },
          signal: AbortSignal.timeout(15_000),
        },
      )
    } catch {
      clearAuthCookies(event)
      throw createError({ statusCode: 401, message: 'Session expired — please sign in again' })
    }

    // Rotate cookies with new tokens
    setAuthCookies(event, refreshData.access_token, refreshData.refresh_token)
    accessToken = refreshData.access_token

    // Retry the original request exactly once
    res = await callUpstream(method, upstreamUrl, accessToken, body, extraHeaders, isPdf)

    // If still 401 after refresh, clear and reject — no retry loop
    if (res.status === 401) {
      clearAuthCookies(event)
      throw createError({ statusCode: 401, message: 'Session expired — please sign in again' })
    }
  }

  // ── 7. Forward safe response headers ─────────────────────────────────────
  const responseHeaders: Record<string, string> = {}
  for (const h of FORWARD_RESPONSE_HEADERS) {
    const val = res.headers.get(h)
    if (val) responseHeaders[h] = val
  }
  setResponseHeaders(event, responseHeaders)

  // ── 8. Return response ────────────────────────────────────────────────────
  setResponseStatus(event, res.status)

  if (isPdf && res._data instanceof ArrayBuffer) {
    await send(event, Buffer.from(res._data), 'application/pdf')
    return
  }

  // For non-2xx, surface the upstream error body to the client
  if (res.status >= 400) {
    throw createError({ statusCode: res.status, data: res._data })
  }

  return res._data
})
