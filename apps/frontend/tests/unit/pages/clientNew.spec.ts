import { describe, it, expect, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { mockFetchClient, mockNavigateTo } from '../../setup'
import ClientNew from '../../../pages/clients/new.vue'

// Stub Nuxt auto-imports used in the component
vi.stubGlobal('useApi', () => ({ post: mockFetchClient }))
vi.stubGlobal('useRoute', () => ({ params: {} }))

describe('pages/clients/new.vue', () => {
  it('shows name-error when form is submitted with empty name', async () => {
    const wrapper = mount(ClientNew, {
      global: { stubs: { NuxtLink: { template: '<a><slot /></a>' } } },
    })
    await wrapper.find('form').trigger('submit')
    await flushPromises()
    await vi.waitFor(() => {
      expect(wrapper.find('[data-testid="name-error"]').exists()).toBe(true)
    }, { timeout: 3000 })
    expect(wrapper.find('[data-testid="name-error"]').text()).toContain('Client name is required')
  })

  it('shows email-error for invalid email format', async () => {
    const wrapper = mount(ClientNew, {
      global: { stubs: { NuxtLink: { template: '<a><slot /></a>' } } },
    })
    await wrapper.find('input#client-name').setValue('Acme')
    await wrapper.find('input#client-email').setValue('not-an-email')
    await wrapper.find('form').trigger('submit')
    await flushPromises()
    await vi.waitFor(() => {
      expect(wrapper.find('[data-testid="email-error"]').exists()).toBe(true)
    }, { timeout: 3000 })
    expect(wrapper.find('[data-testid="email-error"]').text()).toContain('Invalid email format')
  })

  it('submits and navigates to /clients on valid form', async () => {
    mockFetchClient.mockResolvedValue({ id: '1', name: 'Acme', email: null, billing_address: null })
    const wrapper = mount(ClientNew, {
      global: { stubs: { NuxtLink: { template: '<a><slot /></a>' } } },
    })
    await wrapper.find('input#client-name').setValue('Acme')
    await wrapper.find('form').trigger('submit')
    await flushPromises()
    await vi.waitFor(() => {
      expect(mockNavigateTo).toHaveBeenCalledWith('/clients')
    }, { timeout: 3000 })
  })
})