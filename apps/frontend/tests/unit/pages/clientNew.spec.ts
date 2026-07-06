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
    // Submit form without filling name — vee-validate validates async
    await wrapper.find('form').trigger('submit')
    await flushPromises()
    await flushPromises()
    const error = wrapper.find('[data-testid="name-error"]')
    expect(error.exists()).toBe(true)
    expect(error.text()).toContain('Client name is required')
  })

  it('shows email-error for invalid email format', async () => {
    const wrapper = mount(ClientNew, {
      global: { stubs: { NuxtLink: { template: '<a><slot /></a>' } } },
    })
    await wrapper.find('input#client-name').setValue('Acme')
    await wrapper.find('input#client-email').setValue('not-an-email')
    await wrapper.find('form').trigger('submit')
    await flushPromises()
    await flushPromises()
    const error = wrapper.find('[data-testid="email-error"]')
    expect(error.exists()).toBe(true)
    expect(error.text()).toContain('Invalid email format')
  })

  it('submits and navigates to /clients on valid form', async () => {
    mockFetchClient.mockResolvedValue({ id: '1', name: 'Acme', email: null, billing_address: null })
    const wrapper = mount(ClientNew, {
      global: { stubs: { NuxtLink: { template: '<a><slot /></a>' } } },
    })
    await wrapper.find('input#client-name').setValue('Acme')
    await wrapper.find('form').trigger('submit')
    await flushPromises()
    await flushPromises()
    expect(mockNavigateTo).toHaveBeenCalledWith('/clients')
  })
})