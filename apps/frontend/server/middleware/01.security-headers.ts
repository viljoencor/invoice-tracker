import { defineEventHandler, setResponseHeaders } from 'h3'

/**
 * Content-Security-Policy notes
 * ─────────────────────────────
 * - script-src 'self'         Compiled Vue bundle only; no eval, no external scripts.
 * - style-src  'unsafe-inline' Required: Tailwind JIT and Vue SFCs inject runtime styles.
 *                              This is a known trade-off documented here.
 * - connect-src 'self'        All API traffic flows through the BFF proxy (same origin).
 * - frame-ancestors 'none'    Replaces X-Frame-Options; prevents clickjacking.
 * - object-src 'none'         Blocks plugins (Flash etc.).
 * - base-uri 'self'           Prevents base-tag injection.
 * - form-action 'self'        Restricts form submissions to same origin.
 */
const CSP = [
  "default-src 'self'",
  "script-src 'self'",
  "style-src 'self' 'unsafe-inline' https://rsms.me",
  "font-src 'self' data: https://rsms.me",
  "img-src 'self' data: blob:",
  "connect-src 'self'",
  "frame-ancestors 'none'",
  "object-src 'none'",
  "base-uri 'self'",
  "form-action 'self'",
].join('; ')

export default defineEventHandler((event) => {
  setResponseHeaders(event, {
    'X-Frame-Options': 'DENY',
    'X-Content-Type-Options': 'nosniff',
    'Referrer-Policy': 'strict-origin-when-cross-origin',
    'Permissions-Policy': 'geolocation=(), camera=(), microphone=()',
    'Content-Security-Policy': CSP,
  })
})
