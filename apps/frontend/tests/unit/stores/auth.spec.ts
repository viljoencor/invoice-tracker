import { describe, it, expect } from 'vitest'
import { mockNavigateTo, $fetchMock } from '../../setup'
import { useAuth } from '../../../composables/useAuth'

describe('useAuth', () => {
  it('isAuthenticated is false when session cookie is null', () => {
    const { isAuthenticated } = useAuth()
    expect(isAuthenticated.value).toBe(false)
  })

  it('isAuthenticated is false when session cookie is empty string', () => {
    document.cookie = 'session='
    const { isAuthenticated } = useAuth()
    expect(isAuthenticated.value).toBe(false)
  })

  it('isAuthenticated is true when session cookie equals "1"', () => {
    document.cookie = 'session=1'
    const { isAuthenticated } = useAuth()
    expect(isAuthenticated.value).toBe(true)
  })

  it('logout calls the BFF logout endpoint', async () => {
    document.cookie = 'session=1'
    const { logout } = useAuth()
    await logout()
    expect($fetchMock).toHaveBeenCalledWith(
      '/api/auth/logout',
      expect.objectContaining({ method: 'POST' }),
    )
  })

  it('logout navigates to /login', async () => {
    document.cookie = 'session=1'
    const { logout } = useAuth()
    await logout()
    expect(mockNavigateTo).toHaveBeenCalledWith('/login')
  })
})