import { defineEventHandler, getCookie } from 'h3'
import { clearAuthCookies } from '../../utils/cookies'
import { getBackendBase } from '../../utils/backend'

export default defineEventHandler(async (event) => {
  const rt = getCookie(event, 'rt')
  const base = getBackendBase()

  if (rt) {
    // Best-effort revocation: if the backend is temporarily unavailable, we still
    // clear the local cookies so the browser session ends.
    try {
      await $fetch(`${base}/auth/logout`, {
        method: 'POST',
        body: { refresh_token: rt },
        headers: { 'Content-Type': 'application/json' },
        signal: AbortSignal.timeout(10_000),
      })
    } catch { /* intentional: logout must always succeed locally */ }
  }

  clearAuthCookies(event)
  return { ok: true }
})
