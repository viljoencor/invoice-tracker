import { defineEventHandler, readBody, createError } from 'h3'
import { setAuthCookies } from '../../utils/cookies'
import { getBackendBase } from '../../utils/backend'

export default defineEventHandler(async (event) => {
  // BFF login: stores tokens in httpOnly cookies so they are never accessible to client JS (prevents XSS token theft).
  // Step 1: Validate email + password present in body.
  const body = await readBody<{ email: string; password: string }>(event)

  if (!body?.email || !body?.password) {
    throw createError({ statusCode: 400, message: 'Email and password are required' })
  }

  // Step 2: Forward credentials to backend /auth/login.
  const base = getBackendBase()

  let data: { access_token: string; refresh_token: string }
  try {
    data = await $fetch<{ access_token: string; refresh_token: string }>(
      `${base}/auth/login`,
      {
        method: 'POST',
        body: { email: body.email, password: body.password },
        headers: { 'Content-Type': 'application/json' },
        signal: AbortSignal.timeout(15_000),
      },
    )
  } catch (e: any) {
    const status = e?.status ?? e?.statusCode ?? 401
    const raw = e?.data?.detail ?? e?.message ?? 'Login failed'
    const message = typeof raw === 'string' ? raw : 'Login failed'
    throw createError({ statusCode: status >= 400 ? status : 401, message })
  }

  // Step 3: Store tokens in httpOnly cookies; never expose them in the response body.
  setAuthCookies(event, data.access_token, data.refresh_token)

  // Deliberately return no token data — cookies are the only channel
  return { ok: true }
})
