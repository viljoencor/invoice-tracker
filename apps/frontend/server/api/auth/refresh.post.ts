import { defineEventHandler, getCookie, createError } from 'h3'
import { setAuthCookies, clearAuthCookies } from '../../utils/cookies'
import { getBackendBase } from '../../utils/backend'

export default defineEventHandler(async (event) => {
  // BFF token refresh: rotates token pair server-side without ever exposing tokens to client JavaScript.
  // Step 1: Read refresh token cookie; reject immediately if absent.
  const rt = getCookie(event, 'rt')
  if (!rt) {
    clearAuthCookies(event)
    throw createError({ statusCode: 401, message: 'No refresh token present' })
  }

  // Step 2: Call backend /auth/refresh with the stored refresh token.
  const base = getBackendBase()

  let data: { access_token: string; refresh_token: string }
  try {
    data = await $fetch<{ access_token: string; refresh_token: string }>(
      `${base}/auth/refresh`,
      {
        method: 'POST',
        body: { refresh_token: rt },
        headers: { 'Content-Type': 'application/json' },
        signal: AbortSignal.timeout(15_000),
      },
    )
  } catch (e: any) {
    // Step 3: On failure clear cookies and force re-login.
    clearAuthCookies(event)
    const status = e?.status ?? e?.statusCode ?? 401
    throw createError({
      statusCode: status >= 400 ? status : 401,
      message: 'Session expired — please sign in again',
    })
  }

  // Step 4: Rotate cookies with new token pair; return ok.
  setAuthCookies(event, data.access_token, data.refresh_token)
  return { ok: true }
})
