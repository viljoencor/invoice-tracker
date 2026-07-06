import { describe, it, expect } from 'vitest'
import { mockToken, mockNavigateTo } from '../../setup'
// Middleware uses defineNuxtRouteMiddleware stub which returns the function unchanged
import authMiddleware from '../../../middleware/auth'

describe('auth middleware', () => {
  it('redirects to /login when no token and route is not /login', () => {
    mockToken.value = null
    authMiddleware({ path: '/invoices' } as any)
    expect(mockNavigateTo).toHaveBeenCalledWith('/login')
  })

  it('redirects to /login when no token and route is /', () => {
    mockToken.value = null
    authMiddleware({ path: '/' } as any)
    expect(mockNavigateTo).toHaveBeenCalledWith('/login')
  })

  it('redirects to /dashboard when token is present and route is /login', () => {
    mockToken.value = 'valid-jwt'
    authMiddleware({ path: '/login' } as any)
    expect(mockNavigateTo).toHaveBeenCalledWith('/dashboard')
  })

  it('does not redirect when token is present on a protected route', () => {
    mockToken.value = 'valid-jwt'
    const result = authMiddleware({ path: '/dashboard' } as any)
    expect(result).toBeUndefined()
    expect(mockNavigateTo).not.toHaveBeenCalled()
  })

  it('does not redirect when visiting /login with no token', () => {
    mockToken.value = null
    const result = authMiddleware({ path: '/login' } as any)
    expect(result).toBeUndefined()
    expect(mockNavigateTo).not.toHaveBeenCalled()
  })
})
