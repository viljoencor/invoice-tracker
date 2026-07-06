import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { defineComponent, h, ref, nextTick } from 'vue'
import AppErrorBoundary from '../../../components/AppErrorBoundary.vue'

/** Throws every time it renders */
const AlwaysThrows = defineComponent({
  render() {
    throw new Error('deliberate render error')
  },
})

describe('AppErrorBoundary', () => {
  it('renders slot content when no error', () => {
    const wrapper = mount(AppErrorBoundary, {
      slots: { default: '<div data-testid="slot-content">Hello</div>' },
    })
    expect(wrapper.find('[data-testid="slot-content"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="error-boundary-fallback"]').exists()).toBe(false)
  })

  it('renders multiple slot elements without error', () => {
    const wrapper = mount(AppErrorBoundary, {
      slots: { default: '<p>One</p><p>Two</p>' },
    })
    expect(wrapper.find('[data-testid="error-boundary-fallback"]').exists()).toBe(false)
  })

  it('shows fallback UI when child component throws on render', async () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

    const wrapper = mount(AppErrorBoundary, {
      slots: { default: AlwaysThrows },
    })
    await nextTick()

    expect(wrapper.find('[data-testid="error-boundary-fallback"]').exists()).toBe(true)
    consoleSpy.mockRestore()
  })

  it('shows retry and home buttons in fallback', async () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

    const wrapper = mount(AppErrorBoundary, {
      slots: { default: AlwaysThrows },
    })
    await nextTick()

    expect(wrapper.find('[data-testid="error-boundary-retry"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="error-boundary-home"]').exists()).toBe(true)
    consoleSpy.mockRestore()
  })

  it('recovers and re-renders slot when child stops throwing after retry', async () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
    const shouldThrow = ref(true)

    const ConditionalThrower = defineComponent({
      render() {
        if (shouldThrow.value) throw new Error('conditional error')
        return h('div', { 'data-testid': 'recovered-content' }, 'All good')
      },
    })

    const wrapper = mount(AppErrorBoundary, {
      slots: { default: ConditionalThrower },
    })
    await nextTick()
    expect(wrapper.find('[data-testid="error-boundary-fallback"]').exists()).toBe(true)

    // Stop throwing before clicking retry so the re-render succeeds
    shouldThrow.value = false
    await wrapper.find('[data-testid="error-boundary-retry"]').trigger('click')
    await nextTick()

    expect(wrapper.find('[data-testid="error-boundary-fallback"]').exists()).toBe(false)
    expect(wrapper.find('[data-testid="recovered-content"]').exists()).toBe(true)
    consoleSpy.mockRestore()
  })

  it('emits error event when child throws', async () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

    const wrapper = mount(AppErrorBoundary, {
      slots: { default: AlwaysThrows },
    })
    await nextTick()

    const emitted = wrapper.emitted('error')
    expect(emitted).toBeTruthy()
    expect((emitted![0][0] as Error).message).toBe('deliberate render error')
    consoleSpy.mockRestore()
  })
})
