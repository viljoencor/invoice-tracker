import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { $fetchMock } from '../../setup'
import Login from '../../../pages/login.vue'

describe('pages/login.vue', () => {
  beforeEach(() => {
    // window.location.href assignment triggers real navigation in some DOM
    // implementations; replace it with a plain writable object for the test.
    // @ts-expect-error - test-only override
    delete window.location
    // @ts-expect-error - test-only override
    window.location = { href: '' }
  })

  it('renders the sign-in form', () => {
    const wrapper = mount(Login)
    expect(wrapper.find('[data-testid="login-email"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="login-password"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="login-submit"]').exists()).toBe(true)
  })

  it('links to the register page', () => {
    const wrapper = mount(Login)
    expect(wrapper.find('[data-testid="login-register-link"]').exists()).toBe(true)
  })

  it('calls the BFF login endpoint with the entered credentials and redirects on success', async () => {
    $fetchMock.mockResolvedValueOnce({ ok: true })
    const wrapper = mount(Login)

    await wrapper.find('[data-testid="login-email"]').setValue('admin@example.com')
    await wrapper.find('[data-testid="login-password"]').setValue('admin123')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect($fetchMock).toHaveBeenCalledWith(
      '/api/auth/login',
      expect.objectContaining({
        method: 'POST',
        body: { email: 'admin@example.com', password: 'admin123' },
        credentials: 'include',
      }),
    )
    expect(window.location.href).toBe('/')
  })

  it('shows an error message and does not redirect on invalid credentials', async () => {
    $fetchMock.mockRejectedValueOnce({ data: { detail: 'Invalid credentials' } })
    const wrapper = mount(Login)

    await wrapper.find('[data-testid="login-email"]').setValue('admin@example.com')
    await wrapper.find('[data-testid="login-password"]').setValue('wrong')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(wrapper.find('[data-testid="login-error"]').text()).toContain('Invalid credentials')
    expect(window.location.href).toBe('')
  })

  it('disables the submit button and shows a signing-in label while the request is in flight', async () => {
    let resolveFetch: (v: unknown) => void = () => {}
    $fetchMock.mockReturnValueOnce(new Promise((resolve) => { resolveFetch = resolve }))
    const wrapper = mount(Login)

    await wrapper.find('[data-testid="login-email"]').setValue('admin@example.com')
    await wrapper.find('[data-testid="login-password"]').setValue('admin123')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    const button = wrapper.find('[data-testid="login-submit"]')
    expect(button.attributes('disabled')).toBeDefined()
    expect(button.text()).toContain('Signing in')

    resolveFetch({ ok: true })
    await flushPromises()
  })
})
