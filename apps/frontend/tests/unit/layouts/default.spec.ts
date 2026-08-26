import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import DefaultLayout from '../../../layouts/default.vue'

const mockLogout = vi.fn()

vi.mock('../../../composables/useAuth', () => ({
  useAuth: () => ({ logout: mockLogout }),
}))

describe('layouts/default.vue — navigation', () => {
  function mountLayout() {
    return mount(DefaultLayout, {
      global: {
        stubs: {
          AppErrorBoundary: { template: '<slot />' },
          NuxtLink: {
            template: '<a :data-to="to"><slot /></a>',
            props: ['to', 'activeClass', 'exactActiveClass'],
          },
        },
      },
    })
  }

  it('renders a Dashboard nav link pointing to /', () => {
    const wrapper = mountLayout()
    const link = wrapper.find('[data-testid="nav-dashboard"]')
    expect(link.exists()).toBe(true)
    expect(link.attributes('data-to')).toBe('/')
  })

  it('renders an Invoices nav link pointing to /invoices', () => {
    const wrapper = mountLayout()
    const link = wrapper.find('[data-testid="nav-invoices"]')
    expect(link.exists()).toBe(true)
    expect(link.attributes('data-to')).toBe('/invoices')
  })

  it('renders a Clients nav link pointing to /clients', () => {
    const wrapper = mountLayout()
    const link = wrapper.find('[data-testid="nav-clients"]')
    expect(link.exists()).toBe(true)
    expect(link.attributes('data-to')).toBe('/clients')
  })

  it('renders a sign-out button', () => {
    const wrapper = mountLayout()
    expect(wrapper.find('[data-testid="logout-button"]').exists()).toBe(true)
  })

  it('calls logout when sign-out button is clicked', async () => {
    const wrapper = mountLayout()
    await wrapper.find('[data-testid="logout-button"]').trigger('click')
    expect(mockLogout).toHaveBeenCalled()
  })

  it('hamburger button toggles mobile menu visibility', async () => {
    const wrapper = mountLayout()
    expect(wrapper.find('[data-testid="nav-mobile-menu"]').exists()).toBe(false)
    await wrapper.find('[data-testid="nav-hamburger"]').trigger('click')
    expect(wrapper.find('[data-testid="nav-mobile-menu"]').exists()).toBe(true)
    await wrapper.find('[data-testid="nav-hamburger"]').trigger('click')
    expect(wrapper.find('[data-testid="nav-mobile-menu"]').exists()).toBe(false)
  })

  it('mobile menu has correct aria-expanded attribute', async () => {
    const wrapper = mountLayout()
    const btn = wrapper.find('[data-testid="nav-hamburger"]')
    expect(btn.attributes('aria-expanded')).toBe('false')
    await btn.trigger('click')
    expect(btn.attributes('aria-expanded')).toBe('true')
  })
})