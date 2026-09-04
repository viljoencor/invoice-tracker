import { describe, it, expect, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { ref, defineComponent, h, Suspense } from 'vue'
import { mockFetchClient } from '../../setup'
import InvoiceIndex from '../../../pages/invoices/index.vue'

const mockUseAsyncData = vi.fn()
vi.stubGlobal('useAsyncData', mockUseAsyncData)
vi.stubGlobal('useApi', () => ({ get: mockFetchClient }))

function mountSuspended() {
  return mount(
    defineComponent({
      render: () => h(Suspense, null, { default: () => h(InvoiceIndex) }),
    }),
    {
      global: { stubs: { NuxtLink: { template: '<a><slot /></a>' } } },
    },
  )
}

describe('pages/invoices/index.vue — data states', () => {
  it('shows loading state while pending', async () => {
    mockUseAsyncData.mockResolvedValue({
      data: ref([]),
      pending: ref(true),
      error: ref(null),
      refresh: vi.fn(),
    })
    const wrapper = mountSuspended()
    await flushPromises()
    expect(wrapper.find('[data-testid="invoices-loading"]').exists()).toBe(true)
  })

  it('shows error state on failure', async () => {
    mockUseAsyncData.mockResolvedValue({
      data: ref([]),
      pending: ref(false),
      error: ref(new Error('Network error')),
      refresh: vi.fn(),
    })
    const wrapper = mountSuspended()
    await flushPromises()
    expect(wrapper.find('[data-testid="invoices-error"]').exists()).toBe(true)
  })

  it('renders no rows when the invoice list is empty', async () => {
    mockUseAsyncData.mockResolvedValue({
      data: ref([]),
      pending: ref(false),
      error: ref(null),
      refresh: vi.fn(),
    })
    const wrapper = mountSuspended()
    await flushPromises()
    expect(wrapper.findAll('tbody [data-testid^="invoice-row-"]').length).toBe(0)
  })

  it('renders invoice rows with number, client, and status when data is loaded', async () => {
    mockUseAsyncData.mockResolvedValue({
      data: ref([
        {
          id: 'inv-1',
          number: 'INV-2026-00001',
          client_name: 'Acme Pty Ltd',
          issue_date: '2026-01-01',
          due_date: '2026-01-31',
          total_cents: 11500,
          balance_cents: 11500,
          status: 'draft',
          currency: 'ZAR',
        },
      ]),
      pending: ref(false),
      error: ref(null),
      refresh: vi.fn(),
    })
    const wrapper = mountSuspended()
    await flushPromises()
    expect(wrapper.find('[data-testid="invoice-row-inv-1"]').exists()).toBe(true)
    expect(wrapper.text()).toContain('INV-2026-00001')
    expect(wrapper.text()).toContain('Acme Pty Ltd')
    expect(wrapper.text()).toContain('draft')
  })
})
