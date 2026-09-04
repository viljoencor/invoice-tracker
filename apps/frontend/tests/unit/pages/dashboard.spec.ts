import { describe, it, expect, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { ref, defineComponent, h, Suspense } from 'vue'
import { mockFetchClient } from '../../setup'
import Dashboard from '../../../pages/index.vue'

vi.stubGlobal('useApi', () => ({ get: mockFetchClient }))

const emptySummary = {
  total_billed_cents: 0,
  total_due_cents: 0,
  overdue_count: 0,
  pending_count: 0,
  bkt_0_30: null,
  bkt_31_60: null,
  bkt_61_90: null,
  bkt_90p: null,
  revenue_by_month: [],
}

function stubAsyncData(summary: unknown, pending: boolean, error: unknown, recentInvoices: unknown[] = []) {
  vi.stubGlobal('useAsyncData', vi.fn((key: string) => {
    if (key === 'dash-summary') {
      return Promise.resolve({
        data: ref(summary),
        pending: ref(pending),
        error: ref(error),
        refresh: vi.fn(),
      })
    }
    return Promise.resolve({
      data: ref(recentInvoices),
      pending: ref(false),
      error: ref(null),
      refresh: vi.fn(),
    })
  }))
}

function mountSuspended() {
  return mount(
    defineComponent({
      render: () => h(Suspense, null, { default: () => h(Dashboard) }),
    }),
    {
      global: { stubs: { NuxtLink: { template: '<a><slot /></a>' } } },
    },
  )
}

describe('pages/index.vue (dashboard)', () => {
  it('shows a loading indicator while the summary is pending', async () => {
    stubAsyncData(emptySummary, true, null)
    const wrapper = mountSuspended()
    await flushPromises()
    expect(wrapper.text()).toContain('Loading')
  })

  it('shows an error message when the summary fails to load', async () => {
    stubAsyncData(emptySummary, false, new Error('boom'))
    const wrapper = mountSuspended()
    await flushPromises()
    expect(wrapper.text()).toContain('Failed to load summary')
  })

  it('renders KPI cards and an empty recent-invoices state once loaded', async () => {
    stubAsyncData(
      { ...emptySummary, total_due_cents: 50000, overdue_count: 2, pending_count: 3 },
      false,
      null,
      [],
    )
    const wrapper = mountSuspended()
    await flushPromises()
    expect(wrapper.text()).toContain('Outstanding')
    expect(wrapper.text()).toContain('Overdue')
    expect(wrapper.text()).toContain('No recent invoices yet')
  })

  it('renders recent invoice rows when present', async () => {
    stubAsyncData(emptySummary, false, null, [
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
    ])
    const wrapper = mountSuspended()
    await flushPromises()
    expect(wrapper.text()).toContain('Acme Pty Ltd')
    expect(wrapper.text()).toContain('INV-2026-00001')
  })
})
