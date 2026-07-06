import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAuthStore } from '../../../stores/auth'

describe('useAuthStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('has empty string as initial token state', () => {
    const store = useAuthStore()
    expect(store.token).toBe('')
  })

  it('setToken updates the token', () => {
    const store = useAuthStore()
    store.setToken('my-jwt-token')
    expect(store.token).toBe('my-jwt-token')
  })

  it('setToken can be called multiple times', () => {
    const store = useAuthStore()
    store.setToken('first-token')
    store.setToken('second-token')
    expect(store.token).toBe('second-token')
  })

  it('logout clears the token to empty string', () => {
    const store = useAuthStore()
    store.setToken('active-token')
    store.logout()
    expect(store.token).toBe('')
  })

  it('logout on an already-empty store is a no-op', () => {
    const store = useAuthStore()
    store.logout()
    expect(store.token).toBe('')
  })
})
