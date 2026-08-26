import { describe, it, expect } from 'vitest'
import { checkOriginMatchesHost } from '../../../server/utils/csrf'

describe('checkOriginMatchesHost', () => {
  // ── Safe methods ──────────────────────────────────────────────────────────

  it('returns null for GET regardless of headers', () => {
    expect(checkOriginMatchesHost('GET', undefined, undefined)).toBeNull()
  })

  it('returns null for HEAD regardless of headers', () => {
    expect(checkOriginMatchesHost('HEAD', undefined, undefined)).toBeNull()
  })

  it('returns null for OPTIONS regardless of headers', () => {
    expect(checkOriginMatchesHost('OPTIONS', undefined, undefined)).toBeNull()
  })

  // ── Missing headers ───────────────────────────────────────────────────────

  it('returns error when Origin is missing on POST', () => {
    const result = checkOriginMatchesHost('POST', undefined, 'localhost:3000')
    expect(result).toMatch(/Origin header missing/)
  })

  it('returns error when Host is missing on POST', () => {
    const result = checkOriginMatchesHost('POST', 'http://localhost:3000', undefined)
    expect(result).toMatch(/Host header missing/)
  })

  // ── Origin matches host ───────────────────────────────────────────────────

  it('returns null when origin host matches Host for POST', () => {
    expect(
      checkOriginMatchesHost('POST', 'http://localhost:3000', 'localhost:3000'),
    ).toBeNull()
  })

  it('returns null when origin host matches Host for PATCH', () => {
    expect(
      checkOriginMatchesHost('PATCH', 'https://app.example.com', 'app.example.com'),
    ).toBeNull()
  })

  it('returns null when origin host matches Host for DELETE', () => {
    expect(
      checkOriginMatchesHost('DELETE', 'https://app.example.com', 'app.example.com'),
    ).toBeNull()
  })

  // ── Origin does NOT match host ─────────────────────────────────────────────

  it('returns error when origin host differs from Host', () => {
    const result = checkOriginMatchesHost(
      'POST',
      'https://evil.example.com',
      'app.example.com',
    )
    expect(result).toMatch(/CSRF check failed/)
    expect(result).toMatch(/evil\.example\.com/)
  })

  it('returns error for cross-origin POST from a different port', () => {
    const result = checkOriginMatchesHost(
      'POST',
      'http://localhost:4000',
      'localhost:3000',
    )
    expect(result).toMatch(/CSRF check failed/)
  })

  // ── Invalid origin ────────────────────────────────────────────────────────

  it('returns error when Origin is not a valid URL', () => {
    const result = checkOriginMatchesHost('POST', 'not-a-url', 'localhost:3000')
    expect(result).toMatch(/invalid Origin/)
  })
})
