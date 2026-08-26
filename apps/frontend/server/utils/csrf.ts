/**
 * Pure CSRF validation utility — no H3 dependency so it can be unit-tested directly.
 *
 * Strategy: for state-changing HTTP methods, require that the Origin header matches
 * the Host header (same-origin check).  GET/HEAD/OPTIONS are safe methods and are
 * skipped.  SameSite=Lax cookies provide the complementary browser-level protection.
 *
 * @returns null when validation passes, or an error message string when it fails.
 */
export function checkOriginMatchesHost(
  method: string,
  origin: string | undefined,
  host: string | undefined,
): string | null {
  const upperMethod = method.toUpperCase()
  if (['GET', 'HEAD', 'OPTIONS'].includes(upperMethod)) return null

  if (!origin) return 'CSRF check failed: Origin header missing'
  if (!host) return 'CSRF check failed: Host header missing'

  let originHost: string
  try {
    originHost = new URL(origin).host
  } catch {
    return 'CSRF check failed: invalid Origin value'
  }

  if (originHost !== host) {
    return `CSRF check failed: origin "${originHost}" does not match host "${host}"`
  }

  return null
}
