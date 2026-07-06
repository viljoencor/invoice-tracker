import type { H3Event } from 'h3'
import { setCookie, deleteCookie } from 'h3'

const IS_PROD = process.env.NODE_ENV === 'production'

/** Shared base options for httpOnly token cookies. */
const SECURE_OPTS = {
  httpOnly: true,
  secure: IS_PROD,
  sameSite: 'lax' as const,
  path: '/',
}

/**
 * Set access-token, refresh-token (both httpOnly), and a client-readable
 * session-indicator cookie.  Never returns token values in responses.
 */
export function setAuthCookies(
  event: H3Event,
  accessToken: string,
  refreshToken: string,
): void {
  // Access token: short-lived (30 min)
  setCookie(event, 'at', accessToken, { ...SECURE_OPTS, maxAge: 30 * 60 })
  // Refresh token: long-lived (12 h)
  setCookie(event, 'rt', refreshToken, { ...SECURE_OPTS, maxAge: 12 * 60 * 60 })
  // Session indicator: client JS reads this to know whether a session exists.
  // Not httpOnly because client code needs to see it.
  // Lifetime matches the refresh token so the UI stays consistent.
  setCookie(event, 'session', '1', {
    httpOnly: false,
    secure: IS_PROD,
    sameSite: 'lax',
    path: '/',
    maxAge: 12 * 60 * 60,
  })
}

/** Clear all auth cookies — called on logout or when tokens become invalid. */
export function clearAuthCookies(event: H3Event): void {
  const opts = { path: '/', secure: IS_PROD, sameSite: 'lax' as const }
  deleteCookie(event, 'at', opts)
  deleteCookie(event, 'rt', opts)
  deleteCookie(event, 'session', opts)
}
