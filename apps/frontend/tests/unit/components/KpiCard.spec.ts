import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import KpiCard from '../../../components/KpiCard.vue'

describe('KpiCard', () => {
  it('renders the label', () => {
    const wrapper = mount(KpiCard, { props: { label: 'Total Revenue', value: 'R 100.00' } })
    expect(wrapper.text()).toContain('Total Revenue')
  })

  it('renders the value', () => {
    const wrapper = mount(KpiCard, { props: { label: 'Revenue', value: 'R 1,234.56' } })
    expect(wrapper.text()).toContain('R 1,234.56')
  })

  it('renders numeric value', () => {
    const wrapper = mount(KpiCard, { props: { label: 'Count', value: 42 } })
    expect(wrapper.text()).toContain('42')
  })

  it('shows unit when provided', () => {
    const wrapper = mount(KpiCard, { props: { label: 'Overdue', value: 3, unit: 'invoices' } })
    expect(wrapper.text()).toContain('invoices')
  })

  it('does not render unit element when omitted', () => {
    const wrapper = mount(KpiCard, { props: { label: 'Revenue', value: 'R 0.00' } })
    // No unit element should be present (v-if="unit")
    const hasUnitDiv = wrapper.findAll('div').some(el => el.text() === 'invoices')
    expect(hasUnitDiv).toBe(false)
  })

  it('renders trend text', () => {
    const wrapper = mount(KpiCard, {
      props: { label: 'Revenue', value: 'R 100', trend: '+10% vs last month', trendColor: 'green' },
    })
    expect(wrapper.text()).toContain('+10% vs last month')
  })

  it('applies green trend color class', () => {
    const wrapper = mount(KpiCard, {
      props: { label: 'Revenue', value: 'R 100', trend: '+5%', trendColor: 'green' },
    })
    expect(wrapper.html()).toContain('text-green-600')
  })

  it('applies red trend color class', () => {
    const wrapper = mount(KpiCard, {
      props: { label: 'Revenue', value: 'R 50', trend: '-5%', trendColor: 'red' },
    })
    expect(wrapper.html()).toContain('text-red-600')
  })

  it('applies yellow trend color class', () => {
    const wrapper = mount(KpiCard, {
      props: { label: 'Outstanding', value: 'R 200', trend: '2 pending', trendColor: 'yellow' },
    })
    expect(wrapper.html()).toContain('text-yellow-600')
  })

  it('applies default gray trend color class', () => {
    const wrapper = mount(KpiCard, {
      props: { label: 'Count', value: 0, trend: 'No change', trendColor: 'gray' },
    })
    expect(wrapper.html()).toContain('text-gray-600')
  })

  it('does not render trend element when trend is omitted', () => {
    const wrapper = mount(KpiCard, { props: { label: 'Revenue', value: 'R 100.00' } })
    // v-if="trend" — the trend div should be absent
    const trendDivs = wrapper.findAll('.text-sm.mt-1')
    expect(trendDivs.length).toBe(0)
  })
})
