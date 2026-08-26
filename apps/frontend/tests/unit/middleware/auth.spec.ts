import { describe, it, expect } from 'vitest'
import { mockNavigateTo } from '../../setup'
// Middleware uses defineNuxtRouteMiddleware stub which returns the function unchanged
import authMiddleware from '../../../middleware/auth'

describe('auth middleware', () => {
  it('redirects to /login when no token and route is not /login', () => {
    authMiddleware({ path: '/invoices' } as any, {} as any)
    expect(mockNavigateTo).toHaveBeenCalledWith('/login')
  })

  it('redirects to /login when no token and route is /', () => {
    authMiddleware({ path: '/' } as any, {} as any)
    expect(mockNavigateTo).toHaveBeenCalledWith('/login')
  })

  it('redirects to / when session cookie is "1" and route is /login', () => {
    document.cookie = 'session=1'
    authMiddleware({ path: '/login' } as any, {} as any)
    expect(mockNavigateTo).toHaveBeenCalledWith('/')
  })

  it('does not redirect when session cookie is "1" on a protected route', () => {
    document.cookie = 'session=1'
    const result = authMiddleware({ path: '/invoices' } as any, {} as any)
    expect(result).toBeUndefined()
    expect(mockNavigateTo).not.toHaveBeenCalled()
  })

  it('does not redirect when visiting /login with no token', () => {
    const result = authMiddleware({ path: '/login' } as any, {} as any)
    expect(result).toBeUndefined()
    expect(mockNavigateTo).not.toHaveBeenCalled()
  })
})