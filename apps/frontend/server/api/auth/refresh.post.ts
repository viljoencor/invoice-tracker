import { defineEventHandler, getCookie, createError } from 'h3'
import { setAuthCookies, clearAuthCookies } from '../../utils/cookies'
import { getBackendBase } from '../../utils/backend'

export default defineEventHandler(async (event) => {
  const rt = getCookie(event, 'rt')
  if (!rt) {
    clearAuthCookies(event)
    throw createError({ statusCode: 401, message: 'No refresh token present' })
  }

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
    // Refresh failed — clear all cookies and require re-login
    clearAuthCookies(event)
    const status = e?.status ?? e?.statusCode ?? 401
    throw createError({
      statusCode: status >= 400 ? status : 401,
      message: 'Session expired — please sign in again',
    })
  }

  setAuthCookies(event, data.access_token, data.refresh_token)
  return { ok: true }
})
