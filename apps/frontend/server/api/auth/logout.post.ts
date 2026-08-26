import { defineEventHandler, getCookie } from 'h3'
import { clearAuthCookies } from '../../utils/cookies'
import { getBackendBase } from '../../utils/backend'

export default defineEventHandler(async (event) => {
  // BFF logout: always clears cookies locally even if the backend is unavailable, so the browser session always ends.
  // Step 1: Read refresh token cookie; 
  // Step 2: Best-effort revocation on backend;
  // Step 3: Clear all auth cookies locally so the browser session always ends.
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
