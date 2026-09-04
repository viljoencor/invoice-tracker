import { describe, it, expect } from 'vitest'
import { isAllowedPath } from '../../../server/api/proxy/[...path]'

describe('proxy isAllowedPath (no open proxy)', () => {
  it('allows exact allowlisted paths', () => {
    expect(isAllowedPath('/clients')).toBe(true)
    expect(isAllowedPath('/invoices')).toBe(true)
    expect(isAllowedPath('/payments')).toBe(true)
    expect(isAllowedPath('/dash')).toBe(true)
    expect(isAllowedPath('/auth/me')).toBe(true)
  })

  it('allows allowlisted paths with a sub-resource segment', () => {
    expect(isAllowedPath('/invoices/123e4567-e89b-12d3-a456-426614174000')).toBe(true)
    expect(isAllowedPath('/invoices/123/pdf')).toBe(true)
    expect(isAllowedPath('/clients/123')).toBe(true)
  })

  it('allows allowlisted paths with a query string', () => {
    expect(isAllowedPath('/payments?invoice_id=123')).toBe(true)
  })

  it('rejects paths outside the allowlist', () => {
    expect(isAllowedPath('/auth/login')).toBe(false)
    expect(isAllowedPath('/auth/register')).toBe(false)
    expect(isAllowedPath('/admin')).toBe(false)
    expect(isAllowedPath('/')).toBe(false)
  })

  it('does not allow a prefix-only match to smuggle an unrelated path', () => {
    // '/invoicesomething' must not match '/invoices' by naive startsWith('/invoices')
    expect(isAllowedPath('/invoicesomething')).toBe(false)
    expect(isAllowedPath('/clientsxyz')).toBe(false)
  })
})
