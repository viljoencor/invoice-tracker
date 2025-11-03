<script setup lang="ts">
import { computed } from 'vue'
import KpiCard from '~/components/KpiCard.vue'
import FancyRevenue from '~/components/RevenueChart.vue'

definePageMeta({ middleware: 'auth' })
const api = useApi()

const { data: summaryData, pending, error } = await useAsyncData(
  'dash-summary',
  () => api.get('/dash/summary'),
  {
    default: () => ({
      total_billed_cents: 0,
      total_due_cents: 0,
      overdue_count: 0,
      revenue_by_month: [] as Array<{ month: string; total_cents: number; count: number }>
    })
  }
)

const { data: recentInvoicesData } = await useAsyncData(
  'recent-invoices',
  () => api.get('/invoices', { params: { limit: 5, sort: '-issue_date' } }),
  { default: () => [] }
)

const { data: invoicesAllMini } = await useAsyncData(
  'invoices-mini',
  () => api.get('/invoices', { params: { limit: 500, sort: '-issue_date' } }),
  { default: () => [] }
)

const summary = computed(() => summaryData.value ?? {})
const recentInvoices = computed<any[]>(() => recentInvoicesData.value ?? [])

/* Helpers */
const ZAR = (rands: number) => new Intl.NumberFormat('en-ZA', { style: 'currency', currency: 'ZAR' }).format(rands)
const fmtDate = (d?: string) => d ? new Date(d).toLocaleDateString('en-ZA', { month: 'short', day: 'numeric', year: 'numeric' }) : ''

/* KPI values */
const outstandingCents = computed(() => Number(summary.value.total_due_cents ?? 0))
const overdueCount = computed(() => Number(summary.value.overdue_count ?? 0))
const pendingCount = computed(() => {
  const rows = (invoicesAllMini.value as any[]) || []
  return rows.filter(r => ['draft', 'sent', 'partially_paid'].includes(String(r.status || '').toLowerCase())).length
})

/* Billed trend chip */
type RevRow = { month: string; total_cents: number; count?: number }
const revenueSeries = computed<RevRow[]>(() => {
  const rows = (summary.value.revenue_by_month ?? []) as RevRow[]
  return [...rows].sort((a, b) => a.month.localeCompare(b.month))
})
const ym = (d: Date) => `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}`
const thisMonthKey = ym(new Date())
const prevMonthKey = ym(new Date(new Date().getFullYear(), new Date().getMonth() - 1, 1))
const thisMonthRevenueCents = computed(() => revenueSeries.value.find(r => r.month === thisMonthKey)?.total_cents ?? 0)
const prevMonthRevenueCents = computed(() => revenueSeries.value.find(r => r.month === prevMonthKey)?.total_cents ?? 0)
const billedTrendPct = computed<number | null>(() => {
  const prev = prevMonthRevenueCents.value
  if (!prev) return null
  const pct = ((thisMonthRevenueCents.value - prev) / prev) * 100
  return Math.round(pct * 10) / 10
})
</script>

<template>
  <div class="p-6 space-y-6">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-semibold">Dashboard</h1>
      <div class="space-x-2">
        <NuxtLink to="/invoices/new" class="px-3 py-2 rounded bg-black text-white">New Invoice</NuxtLink>
        <NuxtLink to="/clients/new" class="px-3 py-2 rounded border border-gray-300">New Client</NuxtLink>
      </div>
    </div>

    <div v-if="pending" class="text-sm text-gray-500">Loading…</div>
    <div v-else-if="error" class="text-sm text-red-600">Failed to load summary</div>

    <template v-else>
      <!-- KPIs -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <KpiCard
          label="Total Billed"
          :value="ZAR(thisMonthRevenueCents / 100)"
          :trend="billedTrendPct === null ? '—' : `${billedTrendPct > 0 ? '+' : ''}${billedTrendPct}% from last month`"
          :trend-color="(billedTrendPct ?? 0) >= 0 ? 'green' : 'red'"
        />
        <KpiCard
          label="Outstanding"
          :value="ZAR(outstandingCents / 100)"
          :trend="`${pendingCount} invoice${pendingCount === 1 ? '' : 's'} pending`"
          :trend-color="outstandingCents > 0 ? 'yellow' : 'green'"
        />
        <KpiCard
          label="Overdue"
          :value="overdueCount"
          unit="invoices"
          :trend-color="overdueCount > 0 ? 'red' : 'green'"
          :trend="overdueCount > 0 ? 'Action needed' : 'All paid on time'"
        />
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <!-- Recent Invoices -->
        <div class="bg-white rounded-2xl shadow overflow-hidden">
          <div class="p-4 border-b flex items-center justify-between">
            <h2 class="text-lg font-semibold">Recent Invoices</h2>
            <NuxtLink to="/invoices" class="text-sm text-gray-600 hover:text-gray-900">
              View all →
            </NuxtLink>
          </div>

          <div v-if="(recentInvoices?.length ?? 0) === 0" class="p-4 text-sm text-gray-500">
            No recent invoices yet
          </div>

          <div v-else class="divide-y">
            <!-- Each row clickable -->
            <NuxtLink
              v-for="inv in recentInvoices"
              :key="inv.id"
              :to="`/invoices/${inv.id}`"
              class="p-4 flex items-center justify-between hover:bg-gray-50 transition"
              :aria-label="`Open invoice ${inv.number}`"
            >
              <div>
                <div class="font-medium">{{ inv.client_name }}</div>
                <div class="text-sm text-gray-600">
                  {{ fmtDate(inv.issue_date) }} · Invoice #{{ inv.number }}
                </div>
              </div>
              <div class="text-right">
                <div class="font-medium">{{ ZAR((inv.total_cents ?? 0) / 100) }}</div>
                <div
                  :class="[
                    'text-sm capitalize',
                    (inv.status || '').toLowerCase() === 'paid' ? 'text-green-600'
                      : (new Date(inv.due_date) < new Date() && (inv.balance_cents ?? 0) > 0) ? 'text-red-600'
                      : 'text-yellow-600'
                  ]"
                >
                  {{ (new Date(inv.due_date) < new Date() && (inv.balance_cents ?? 0) > 0) ? 'Overdue' : (inv.status || 'draft') }}
                </div>
              </div>
            </NuxtLink>
          </div>
        </div>

        <!-- Revenue -->
        <FancyRevenue :data="(summary.revenue_by_month as any[]) || []" :height="220" :max-bars="12">
          <template #chip>
            <span
              v-if="billedTrendPct !== null"
              class="text-[11px] px-2 py-0.5 rounded-full"
              :class="(billedTrendPct ?? 0) >= 0 ? 'bg-green-50 text-green-700 ring-1 ring-green-200' : 'bg-red-50 text-red-700 ring-1 ring-red-200'"
            >
              {{ billedTrendPct > 0 ? '▲' : '▼' }} {{ Math.abs(billedTrendPct) }}% MoM
            </span>
          </template>
        </FancyRevenue>
      </div>
    </template>
  </div>
</template>
