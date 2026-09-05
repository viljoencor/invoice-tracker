import { describe, it, expect, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { ref, defineComponent, h, Suspense } from 'vue'
import InvoiceDetail from '../../../pages/invoices/[id].vue'

const mockGet = vi.fn()
const mockPost = vi.fn()
const mockGetArrayBuffer = vi.fn()

vi.stubGlobal('useApi', () => ({ get: mockGet, post: mockPost, getArrayBuffer: mockGetArrayBuffer }))
vi.stubGlobal('useRoute', () => ({ params: { id: 'inv-1' } }))
vi.stubGlobal('refreshNuxtData', vi.fn())

const baseInvoice = {
  id: 'inv-1',
  number: 'INV-2026-00001',
  client_id: 'c1',
  client_name: 'Acme Pty Ltd',
  issue_date: '2026-01-01',
  due_date: '2026-01-31',
  currency: 'ZAR',
  subtotal_cents: 10000,
  tax_cents: 1500,
  total_cents: 11500,
  balance_cents: 11500,
  status: 'draft',
}

function stubAsyncData(invoice: unknown, pending: boolean, error: unknown) {
  vi.stubGlobal('useAsyncData', vi.fn((key: unknown) => {
    const resolvedKey = typeof key === 'function' ? key() : key
    if (String(resolvedKey).startsWith('payments-')) {
      return Promise.resolve({ data: ref([]), pending: ref(false), error: ref(null), refresh: vi.fn() })
    }
    return Promise.resolve({
      data: ref(invoice),
      pending: ref(pending),
      error: ref(error),
      refresh: vi.fn(),
    })
  }))
}

function mountSuspended() {
  return mount(
    defineComponent({
      render: () => h(Suspense, null, { default: () => h(InvoiceDetail) }),
    }),
    { global: { stubs: { NuxtLink: { template: '<a><slot /></a>' } } } },
  )
}

describe('pages/invoices/[id].vue', () => {
  it('shows a loading state while the invoice is pending', async () => {
    stubAsyncData(null, true, null)
    const wrapper = mountSuspended()
    await flushPromises()
    expect(wrapper.find('[data-testid="invoice-loading"]').exists()).toBe(true)
  })

  it('shows an error state when the invoice fails to load', async () => {
    stubAsyncData(null, false, new Error('boom'))
    const wrapper = mountSuspended()
    await flushPromises()
    expect(wrapper.find('[data-testid="invoice-load-error"]').exists()).toBe(true)
  })

  it('renders invoice details and a Mark as Sent button for a draft invoice', async () => {
    stubAsyncData(baseInvoice, false, null)
    const wrapper = mountSuspended()
    await flushPromises()
    expect(wrapper.text()).toContain('INV-2026-00001')
    expect(wrapper.find('[data-testid="send-invoice-btn"]').exists()).toBe(true)
  })

  it('sends an Idempotency-Key header when recording a payment', async () => {
    stubAsyncData(baseInvoice, false, null)
    mockPost.mockResolvedValue({ status: 'ok' })
    const wrapper = mountSuspended()
    await flushPromises()

    const amountInput = wrapper.find('input[placeholder="e.g. 115.00"]')
    await amountInput.setValue('50.00')
    await wrapper.find('[data-testid="save-payment-btn"]').trigger('click')
    await flushPromises()

    expect(mockPost).toHaveBeenCalledWith(
      '/payments',
      expect.objectContaining({ invoice_id: 'inv-1', amount_cents: 5000 }),
      expect.objectContaining({ headers: expect.objectContaining({ 'Idempotency-Key': expect.any(String) }) }),
    )
  })

  it('rejects a payment amount that exceeds the outstanding balance', async () => {
    stubAsyncData(baseInvoice, false, null)
    const wrapper = mountSuspended()
    await flushPromises()

    const amountInput = wrapper.find('input[placeholder="e.g. 115.00"]')
    await amountInput.setValue('999.00')
    await wrapper.find('[data-testid="save-payment-btn"]').trigger('click')
    await flushPromises()

    expect(wrapper.find('[data-testid="pay-error"]').text()).toContain('exceeds current balance')
    expect(mockPost).not.toHaveBeenCalled()
  })
})
