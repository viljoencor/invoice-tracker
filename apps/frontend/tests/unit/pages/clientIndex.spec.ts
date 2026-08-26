import { describe, it, expect, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { ref, defineComponent, h, Suspense } from 'vue'
import { mockFetchClient } from '../../setup'
import ClientIndex from '../../../pages/clients/index.vue'

const mockUseAsyncData = vi.fn()
vi.stubGlobal('useAsyncData', mockUseAsyncData)
vi.stubGlobal('useApi', () => ({ get: mockFetchClient }))

// Wrap component in Suspense so async setup works
function mountSuspended(propsData = {}) {
  return mount(
    defineComponent({
      render: () => h(Suspense, null, { default: () => h(ClientIndex) }),
    }),
    {
      global: { stubs: { NuxtLink: { template: '<a><slot /></a>' } } },
    },
  )
}

describe('pages/clients/index.vue — data states', () => {
  it('shows loading state while pending', async () => {
    mockUseAsyncData.mockResolvedValue({
      data: ref([]),
      pending: ref(true),
      error: ref(null),
      refresh: vi.fn(),
    })
    const wrapper = mountSuspended()
    await flushPromises()
    expect(wrapper.find('[data-testid="clients-loading"]').exists()).toBe(true)
  })

  it('shows error state and retry button on failure', async () => {
    const refresh = vi.fn()
    mockUseAsyncData.mockResolvedValue({
      data: ref([]),
      pending: ref(false),
      error: ref(new Error('Network error')),
      refresh,
    })
    const wrapper = mountSuspended()
    await flushPromises()
    expect(wrapper.find('[data-testid="clients-error"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="clients-retry"]').exists()).toBe(true)
    await wrapper.find('[data-testid="clients-retry"]').trigger('click')
    expect(refresh).toHaveBeenCalled()
  })

  it('shows empty state when no clients', async () => {
    mockUseAsyncData.mockResolvedValue({
      data: ref([]),
      pending: ref(false),
      error: ref(null),
      refresh: vi.fn(),
    })
    const wrapper = mountSuspended()
    await flushPromises()
    expect(wrapper.find('[data-testid="clients-empty"]').exists()).toBe(true)
  })

  it('shows table with client rows when data is loaded', async () => {
    mockUseAsyncData.mockResolvedValue({
      data: ref([
        { id: 'c1', name: 'Acme', email: 'acme@co.za', billing_address: null },
        { id: 'c2', name: 'Globex', email: null, billing_address: '1 Main St' },
      ]),
      pending: ref(false),
      error: ref(null),
      refresh: vi.fn(),
    })
    const wrapper = mountSuspended()
    await flushPromises()
    expect(wrapper.find('[data-testid="clients-table"]').exists()).toBe(true)
    expect(wrapper.text()).toContain('Acme')
    expect(wrapper.text()).toContain('Globex')
  })
})