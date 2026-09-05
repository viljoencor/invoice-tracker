import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { $fetchMock } from '../../setup'
import Register from '../../../pages/register.vue'

describe('pages/register.vue', () => {
  beforeEach(() => {
    // @ts-expect-error - test-only override, mirrors login.spec.ts
    delete window.location
    // @ts-expect-error - test-only override
    window.location = { href: '' }
  })

  it('renders the registration form', () => {
    const wrapper = mount(Register, { global: { stubs: { NuxtLink: { template: '<a><slot /></a>' } } } })
    expect(wrapper.find('[data-testid="register-name"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="register-email"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="register-password"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="register-submit"]').exists()).toBe(true)
  })

  it('calls the BFF register endpoint with the entered details and redirects on success', async () => {
    $fetchMock.mockResolvedValueOnce({ ok: true })
    const wrapper = mount(Register, { global: { stubs: { NuxtLink: { template: '<a><slot /></a>' } } } })

    await wrapper.find('[data-testid="register-name"]').setValue('Jane Doe')
    await wrapper.find('[data-testid="register-email"]').setValue('jane@example.com')
    await wrapper.find('[data-testid="register-password"]').setValue('hunter22')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect($fetchMock).toHaveBeenCalledWith(
      '/api/auth/register',
      expect.objectContaining({
        method: 'POST',
        body: { name: 'Jane Doe', email: 'jane@example.com', password: 'hunter22' },
        credentials: 'include',
      }),
    )
    expect(window.location.href).toBe('/')
  })

  it('shows an error message and does not redirect when the email is already registered', async () => {
    $fetchMock.mockRejectedValueOnce({ data: { detail: 'Email already registered' } })
    const wrapper = mount(Register, { global: { stubs: { NuxtLink: { template: '<a><slot /></a>' } } } })

    await wrapper.find('[data-testid="register-name"]').setValue('Jane Doe')
    await wrapper.find('[data-testid="register-email"]').setValue('jane@example.com')
    await wrapper.find('[data-testid="register-password"]').setValue('hunter22')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(wrapper.find('[data-testid="register-error"]').text()).toContain('Email already registered')
    expect(window.location.href).toBe('')
  })

  it('links back to the login page', () => {
    const wrapper = mount(Register, { global: { stubs: { NuxtLink: { template: '<a><slot /></a>' } } } })
    expect(wrapper.find('[data-testid="register-login-link"]').exists()).toBe(true)
  })
})
