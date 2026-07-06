/**
 * Global test setup: stubs for Nuxt auto-imported composables and global components.
 * Exports shared reactive state for use in per-test assertions.
 */
import { config } from '@vue/test-utils'
import { vi, beforeEach } from 'vitest'
import { ref } from 'vue'

// ── Global component stubs ────────────────────────────────────────────────────
config.global.stubs = {
  NuxtLink: { template: '<a><slot /></a>' },
  NuxtPage: { template: '<div />' },
  NuxtLayout: { template: '<slot />' },
}

// ── Shared reactive mock state ────────────────────────────────────────────────
/** The reactive cookie token returned by useCookie() stub */
export const mockToken = ref<string | null>(null)
/** Spy for navigateTo() */
export const mockNavigateTo = vi.fn()
/** Spy for clearError() */
export const mockClearError = vi.fn()
/** The fetch function returned by $fetch.create() */
export const mockFetchClient = vi.fn()
/** Spy for $fetch.create() */
export const mockFetchCreate = vi.fn()

// ── Nuxt composable stubs ─────────────────────────────────────────────────────
vi.stubGlobal('useRuntimeConfig', () => ({
  public: { apiBase: 'http://localhost:8000/api/v1' },
}))
vi.stubGlobal('useCookie', (_key: string) => mockToken)
vi.stubGlobal('navigateTo', mockNavigateTo)
vi.stubGlobal('defineNuxtRouteMiddleware', (fn: Function) => fn)
vi.stubGlobal('useError', () => ref(null))
vi.stubGlobal('clearError', mockClearError)
vi.stubGlobal('useNuxtApp', () => ({}))
vi.stubGlobal('definePageMeta', vi.fn())
vi.stubGlobal('useAsyncData', vi.fn().mockResolvedValue({
  data: ref(null),
  pending: ref(false),
  error: ref(null),
}))

// $fetch with .create method
const $fetchMock = Object.assign(vi.fn(), { create: mockFetchCreate })
vi.stubGlobal('$fetch', $fetchMock)

// ── Per-test reset ────────────────────────────────────────────────────────────
beforeEach(() => {
  mockToken.value = null
  vi.clearAllMocks()
  // Restore create() implementation after clearAllMocks (safe — clearAllMocks
  // only wipes call history, not factory-provided implementations, but we
  // re-apply to be explicit).
  mockFetchCreate.mockReturnValue(mockFetchClient)
})
