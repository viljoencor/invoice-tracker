import { defineStore } from 'pinia'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: '' as string,
  }),
  actions: {
    setToken(t: string) { this.token = t },
    logout() { this.token = '' }
  }
})