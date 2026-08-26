import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { ref, defineComponent, h, Suspense, nextTick } from 'vue'
import { mockFetchClient, mockNavigateTo } from '../../setup'

// Dynamic import to avoid Vite glob expansion on [id] brackets
const ClientDetailModule = await import('../../../pages/clients/[id].vue')
const ClientDetail = ClientDetailModule.default

const mockUseAsyncData = vi.fn()
vi.stubGlobal('useAsyncData', mockUseAsyncData)
vi.stubGlobal('useApi', () => ({
  get: mockFetchClient,
  patch: mockFetchClient,
  del: mockFetchClient,
}))
vi.stubGlobal('useRoute', () => ({ params: { id: 'c1' } }))

const stubClient = { id: 'c1', name: 'Acme Corp', email: 'acme@co.za', billing_address: null }

function mountSuspended() {
  return mount(
    defineComponent({
      render: () => h(Suspense, null, { default: () => h(ClientDetail) }),
    }),
    {
      global: { stubs: { NuxtLink: { template: '<a><slot /></a>' } } },
    },
  )
}

describe('pages/clients/[id].vue � client detail', () => {
  beforeEach(() => {
    mockUseAsyncData.mockResolvedValue({
      data: ref(stubClient),
      pending: ref(false),
      error: ref(null),
      refresh: vi.fn(),
    })
  })

  it('shows loading state while pending', async () => {
    mockUseAsyncData.mockResolvedValue({
      data: ref(null),
      pending: ref(true),
      error: ref(null),
      refresh: vi.fn(),
    })
    const wrapper = mountSuspended()
    await flushPromises()
    expect(wrapper.find('[data-testid="client-loading"]').exists()).toBe(true)
  })

  it('shows error state with retry on fetch failure', async () => {
    const refresh = vi.fn()
    mockUseAsyncData.mockResolvedValue({
      data: ref(null),
      pending: ref(false),
      error: ref(new Error('Not found')),
      refresh,
    })
    const wrapper = mountSuspended()
    await flushPromises()
    expect(wrapper.find('[data-testid="client-load-error"]').exists()).toBe(true)
    await wrapper.find('[data-testid="client-retry"]').trigger('click')
    expect(refresh).toHaveBeenCalled()
  })

  it('displays client name in heading', async () => {
    const wrapper = mountSuspended()
    await flushPromises()
    expect(wrapper.find('[data-testid="client-name-heading"]').text()).toBe('Acme Corp')
  })

  it('opens edit form when Edit button is clicked', async () => {
    const wrapper = mountSuspended()
    await flushPromises()
    await wrapper.find('[data-testid="client-edit-btn"]').trigger('click')
    expect(wrapper.find('[data-testid="client-edit-form"]').exists()).toBe(true)
  })

  it('cancels edit mode without saving', async () => {
    const wrapper = mountSuspended()
    await flushPromises()
    await wrapper.find('[data-testid="client-edit-btn"]').trigger('click')
    await wrapper.find('[data-testid="client-cancel-btn"]').trigger('click')
    expect(wrapper.find('[data-testid="client-edit-form"]').exists()).toBe(false)
    expect(wrapper.find('[data-testid="client-detail"]').exists()).toBe(true)
  })

  it('shows validation error when name is cleared in edit form', async () => {
    const wrapper = mountSuspended()
    await flushPromises()
    await wrapper.find('[data-testid="client-edit-btn"]').trigger('click')
    await flushPromises()
    await wrapper.find('#edit-name').setValue('')
    await flushPromises()
    await wrapper.find('[data-testid="client-edit-form"]').trigger('submit')
    await flushPromises()
    await flushPromises()
    await flushPromises()
    await nextTick()
    expect(wrapper.find('[data-testid="client-edit-name-error"]').exists()).toBe(true)
  })

  it('shows confirm dialog when Delete button is clicked', async () => {
    const wrapper = mountSuspended()
    await flushPromises()
    await wrapper.find('[data-testid="client-delete-btn"]').trigger('click')
    expect(wrapper.find('[data-testid="delete-confirm-dialog"]').exists()).toBe(true)
  })

  it('hides confirm dialog on Cancel', async () => {
    const wrapper = mountSuspended()
    await flushPromises()
    await wrapper.find('[data-testid="client-delete-btn"]').trigger('click')
    await wrapper.find('[data-testid="delete-cancel-btn"]').trigger('click')
    expect(wrapper.find('[data-testid="delete-confirm-dialog"]').exists()).toBe(false)
  })

  it('navigates to /clients after successful deletion', async () => {
    mockFetchClient.mockResolvedValue(undefined)
    const wrapper = mountSuspended()
    await flushPromises()
    await wrapper.find('[data-testid="client-delete-btn"]').trigger('click')
    await wrapper.find('[data-testid="delete-confirm-btn"]').trigger('click')
    await flushPromises()
    expect(mockNavigateTo).toHaveBeenCalledWith('/clients')
  })

  it('shows conflict error when delete returns 409', async () => {
    mockFetchClient.mockRejectedValue({ status: 409, data: { detail: 'Client has invoices and cannot be deleted' } })
    const wrapper = mountSuspended()
    await flushPromises()
    await wrapper.find('[data-testid="client-delete-btn"]').trigger('click')
    await wrapper.find('[data-testid="delete-confirm-btn"]').trigger('click')
    await flushPromises()
    expect(wrapper.find('[data-testid="client-delete-error"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="client-delete-error"]').text()).toContain('invoices')
  })
})