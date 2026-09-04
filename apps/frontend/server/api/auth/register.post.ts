import { defineEventHandler, readBody, createError } from 'h3'
import { setAuthCookies } from '../../utils/cookies'
import { getBackendBase } from '../../utils/backend'

export default defineEventHandler(async (event) => {
  // BFF register: creates the org + owner user on the backend, then stores the
  // returned tokens in httpOnly cookies exactly like login — a new account is
  // signed in immediately, never handling tokens in client JS.
  // Step 1: Validate name + email + password present in body.
  const body = await readBody<{ name: string; email: string; password: string }>(event)

  if (!body?.name || !body?.email || !body?.password) {
    throw createError({ statusCode: 400, message: 'Name, email, and password are required' })
  }

  // Step 2: Forward registration details to backend /auth/register.
  const base = getBackendBase()

  let data: { access_token: string; refresh_token: string }
  try {
    data = await $fetch<{ access_token: string; refresh_token: string }>(
      `${base}/auth/register`,
      {
        method: 'POST',
        body: { name: body.name, email: body.email, password: body.password },
        headers: { 'Content-Type': 'application/json' },
        signal: AbortSignal.timeout(15_000),
      },
    )
  } catch (e: any) {
    const status = e?.status ?? e?.statusCode ?? 400
    const raw = e?.data?.detail ?? e?.message ?? 'Registration failed'
    const message = typeof raw === 'string' ? raw : 'Registration failed'
    throw createError({ statusCode: status >= 400 ? status : 400, message })
  }

  // Step 3: Store tokens in httpOnly cookies; never expose them in the response body.
  setAuthCookies(event, data.access_token, data.refresh_token)

  return { ok: true }
})
