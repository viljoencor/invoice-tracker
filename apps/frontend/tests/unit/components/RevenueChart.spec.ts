import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import RevenueChart from '../../../components/RevenueChart.vue'

const sampleData = [
  { month: '2024-01', total_cents: 100000 },
  { month: '2024-02', total_cents: 150000 },
  { month: '2024-03', total_cents: 120000 },
]

describe('RevenueChart', () => {
  it('renders without crashing with empty data', () => {
    const wrapper = mount(RevenueChart, { props: { data: [] } })
    expect(wrapper.find('svg').exists()).toBe(true)
  })

  it('renders svg with data', () => {
    const wrapper = mount(RevenueChart, { props: { data: sampleData } })
    expect(wrapper.find('svg').exists()).toBe(true)
  })

  it('renders the correct number of bars', () => {
    const wrapper = mount(RevenueChart, { props: { data: sampleData } })
    // One <rect> per bar (the bar fill rect)
    const rects = wrapper.findAll('rect')
    expect(rects.length).toBe(sampleData.length)
  })

  it('shows Revenue heading', () => {
    const wrapper = mount(RevenueChart, { props: { data: sampleData } })
    expect(wrapper.text()).toContain('Revenue')
  })

  it('respects maxBars prop — trims to last N bars', () => {
    const manyBars = Array.from({ length: 20 }, (_, i) => ({
      month: `2024-${String(i + 1).padStart(2, '0')}`,
      total_cents: 10000 * (i + 1),
    }))
    const wrapper = mount(RevenueChart, { props: { data: manyBars, maxBars: 6 } })
    expect(wrapper.findAll('rect').length).toBe(6)
  })

  it('renders no bars for empty data', () => {
    const wrapper = mount(RevenueChart, { props: { data: [] } })
    expect(wrapper.findAll('rect').length).toBe(0)
  })

  it('renders a single bar for one-item data', () => {
    const wrapper = mount(RevenueChart, {
      props: { data: [{ month: '2024-01', total_cents: 50000 }] },
    })
    expect(wrapper.findAll('rect').length).toBe(1)
  })

  it('accepts custom height prop without crashing', () => {
    const wrapper = mount(RevenueChart, { props: { data: sampleData, height: 300 } })
    expect(wrapper.find('svg').exists()).toBe(true)
  })

  it('accepts custom currency prop without crashing', () => {
    const wrapper = mount(RevenueChart, { props: { data: sampleData, currency: 'USD' } })
    expect(wrapper.find('svg').exists()).toBe(true)
  })
})
