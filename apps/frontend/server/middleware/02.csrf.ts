import { defineEventHandler, getMethod, getHeader, createError } from 'h3'
import { checkOriginMatchesHost } from '../utils/csrf'

/**
 * CSRF protection via Origin / Host header matching.
 *
 * - Safe methods (GET, HEAD, OPTIONS) are not checked.
 * - State-changing BFF requests require the Origin header to match the Host.
 * - SameSite=Lax cookies provide the complementary browser-level protection.
 */
export default defineEventHandler((event) => {
  const method = getMethod(event)
  const origin = getHeader(event, 'origin')
  const host = getHeader(event, 'host')

  const err = checkOriginMatchesHost(method, origin, host)
  if (err) {
    throw createError({ statusCode: 403, message: err })
  }
})
