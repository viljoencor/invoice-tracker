import { ref } from 'vue'
import { defineStore } from 'pinia'
import type { ClientOut } from '~/types/api'

export const useClientsStore = defineStore('clients', () => {
  const items = ref<ClientOut[]>([])
  const loaded = ref(false)
  const pending = ref(false)
  const error = ref<unknown>(null)

  async function fetchAll(params?: Record<string, unknown>) {
    const api = useApi()
    pending.value = true
    error.value = null
    try {
      items.value = await api.get<ClientOut[]>('/clients', { params })
      loaded.value = true
    } catch (e) {
      error.value = e
    } finally {
      pending.value = false
    }
  }

  /** Mark the cache stale so the next fetchAll re-requests from the API. */
  function invalidate() {
    loaded.value = false
  }

  return { items, loaded, pending, error, fetchAll, invalidate }
})
