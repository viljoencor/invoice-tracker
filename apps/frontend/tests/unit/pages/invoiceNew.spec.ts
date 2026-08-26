import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { ref } from 'vue'
import { mockFetchClient } from '../../setup'
import InvoiceNew from '../../../pages/invoices/new.vue'

// Stub Nuxt auto-imports
vi.stubGlobal('useApi', () => ({ get: mockFetchClient, post: mockFetchClient }))
vi.stubGlobal('onMounted', (fn: () => void) => fn())
vi.stubGlobal('useRoute', () => ({ params: {} }))

describe('pages/invoices/new.vue', () => {
  beforeEach(() => {
    mockFetchClient.mockResolvedValue([])
  })

  it('shows due-date-error when due date is before issue date', async () => {
    const wrapper = mount(InvoiceNew, {
      global: { stubs: { NuxtLink: { template: '<a><slot /></a>' } } },
    })
    await flushPromises()
    ;(wrapper.vm as any).form.issue_date = '2024-06-01'
    ;(wrapper.vm as any).form.due_date = '2024-05-01'
    ;(wrapper.vm as any).form.client_id = 'client-1'
    ;(wrapper.vm as any).form.items = [{ description: 'Work', qty: 1, unit_price_cents: 10000, tax_rate_bp: 0 }]
    // Call submit directly (bypassing disabled guard)
    await (wrapper.vm as any).submit()
    await flushPromises()
    const error = wrapper.find('[data-testid="due-date-error"]')
    expect(error.exists()).toBe(true)
    expect(error.text()).toContain('Due date cannot be before issue date')
  })

  it('shows items-error when no line items', async () => {
    const wrapper = mount(InvoiceNew, {
      global: { stubs: { NuxtLink: { template: '<a><slot /></a>' } } },
    })
    await flushPromises()
    ;(wrapper.vm as any).form.client_id = 'client-1'
    ;(wrapper.vm as any).form.issue_date = '2024-06-01'
    ;(wrapper.vm as any).form.due_date = '2024-06-30'
    ;(wrapper.vm as any).form.items = []
    await (wrapper.vm as any).submit()
    await flushPromises()
    const error = wrapper.find('[data-testid="items-error"]')
    expect(error.exists()).toBe(true)
    expect(error.text()).toContain('At least one line item')
  })
})