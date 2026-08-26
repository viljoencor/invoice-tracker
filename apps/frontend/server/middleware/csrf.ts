import { defineEventHandler, getMethod, getHeader, createError } from 'h3'
import { checkOriginMatchesHost } from '../utils/csrf'

export default defineEventHandler((event) => {
  // In dev, nuxt dev binds on a random internal port so Host never matches the
  // browser Origin. SameSite=Lax cookies still provide CSRF protection in dev.
  if (process.env.NODE_ENV !== 'production') return

  const method = getMethod(event)
  const origin = getHeader(event, 'origin')
  const host = getHeader(event, 'host')

  const err = checkOriginMatchesHost(method, origin, host)
  if (err) {
    throw createError({ statusCode: 403, message: err })
  }
})
