import { describe, it, expect } from 'vitest'
import { mockToken, mockNavigateTo } from '../../setup'
import { useAuth } from '../../../composables/useAuth'

describe('useAuth', () => {
  it('isAuthenticated is false when token is null', () => {
    mockToken.value = null
    const { isAuthenticated } = useAuth()
    expect(isAuthenticated.value).toBe(false)
  })

  it('isAuthenticated is false when token is empty string', () => {
    mockToken.value = ''
    const { isAuthenticated } = useAuth()
    expect(isAuthenticated.value).toBe(false)
  })

  it('isAuthenticated is true when token has value', () => {
    mockToken.value = 'valid-jwt'
    const { isAuthenticated } = useAuth()
    expect(isAuthenticated.value).toBe(true)
  })

  it('token ref reflects the cookie value', () => {
    mockToken.value = 'abc123'
    const { token } = useAuth()
    expect(token.value).toBe('abc123')
  })

  it('logout clears token and navigates to /login', async () => {
    mockToken.value = 'valid-jwt'
    const { logout } = useAuth()
    await logout()
    expect(mockToken.value).toBeNull()
    expect(mockNavigateTo).toHaveBeenCalledWith('/login')
  })
})