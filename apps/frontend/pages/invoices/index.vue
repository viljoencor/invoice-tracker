<script setup lang="ts">
import type { InvoiceList } from '~/types/api'

definePageMeta({ middleware: 'auth' })

import { ref } from 'vue'
import { useApi } from '~/composables/useApi'

const api = useApi()

// Always return an array so v-for can render immediately
const { data: invoices, pending, error, refresh } = await useAsyncData<InvoiceList[]>(
  'invoices',
  () => api.get<InvoiceList[]>('/invoices', { params: { sort: '-issue_date', limit: 50 } }),
  { default: (): InvoiceList[] => [] },
)

function formatCurrency(amount: number): string {
  return new Intl.NumberFormat('en-ZA', { style: 'currency', currency: 'ZAR' })
    .format(amount / 100)
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString('en-ZA', { year: 'numeric', month: 'short', day: 'numeric' })
}

const statuses: Record<string, string> = {
  draft: 'bg-gray-100 text-gray-800',
  sent: 'bg-blue-100 text-blue-800',
  paid: 'bg-green-100 text-green-800',
  overdue: 'bg-red-100 text-red-800',
}
</script>

<template>
  <div class="py-6">
    <div class="px-4 sm:px-6 lg:px-8">
      <div class="sm:flex sm:items-center">
        <div class="sm:flex-auto">
          <h1 class="text-2xl font-semibold text-gray-900">Invoices</h1>
        </div>
        <div class="mt-4 sm:mt-0 sm:ml-16 sm:flex-none">
          <NuxtLink
            to="/invoices/new"
            class="inline-flex items-center justify-center rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
          >
            New Invoice
          </NuxtLink>
        </div>
      </div>

      <div class="mt-8 flex flex-col">
        <div class="-my-2 -mx-4 overflow-x-auto sm:-mx-6 lg:-mx-8">
          <div class="inline-block min-w-full py-2 align-middle md:px-6 lg:px-8">
            <div v-if="pending" class="text-sm text-gray-500">Loading…</div>
            <div v-else-if="error" class="text-sm text-red-600">Failed to load invoices</div>

            <div v-else class="overflow-hidden shadow ring-1 ring-black/5 md:rounded-lg">
              <table class="min-w-full divide-y divide-gray-300">
                <thead class="bg-gray-50">
                  <tr>
                    <th class="py-3.5 pl-4 pr-3 text-left text-sm font-semibold text-gray-900 sm:pl-6">Invoice</th>
                    <th class="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">Client</th>
                    <th class="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">Issue Date</th>
                    <th class="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">Due Date</th>
                    <th class="px-3 py-3.5 text-right text-sm font-semibold text-gray-900">Amount</th>
                    <th class="px-3 py-3.5 text-center text-sm font-semibold text-gray-900">Status</th>
                    <th class="relative py-3.5 pl-3 pr-4 sm:pr-6"><span class="sr-only">Actions</span></th>
                  </tr>
                </thead>

                <tbody class="divide-y divide-gray-200 bg-white">
                  <!-- iterate over invoices (auto-unwrapped ref) -->
                  <tr v-for="invoice in invoices" :key="invoice.id">
                    <td class="whitespace-nowrap py-4 pl-4 pr-3 text-sm font-medium text-blue-600 hover:text-blue-900 sm:pl-6">
                      <NuxtLink :to="`/invoices/${invoice.id}`">{{ invoice.number }}</NuxtLink>
                    </td>
                    <td class="whitespace-nowrap px-3 py-4 text-sm text-gray-900">
                      {{ invoice.client_name }}
                    </td>
                    <td class="whitespace-nowrap px-3 py-4 text-sm text-gray-500">
                      {{ formatDate(invoice.issue_date) }}
                    </td>
                    <td class="whitespace-nowrap px-3 py-4 text-sm text-gray-500">
                      {{ formatDate(invoice.due_date) }}
                    </td>
                    <td class="whitespace-nowrap px-3 py-4 text-sm text-right text-gray-900">
                      {{ formatCurrency(invoice.total_cents) }}
                    </td>
                    <td class="whitespace-nowrap px-3 py-4 text-sm text-center">
                      <span class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium capitalize"
                            :class="statuses[(invoice.status || '').toLowerCase()]">
                        {{ invoice.status }}
                      </span>
                    </td>
                    <td class="relative whitespace-nowrap py-4 pl-3 pr-4 text-right text-sm font-medium sm:pr-6">
                      <!-- optional: button to download PDF using authenticated helper, like on the detail page -->
                      <NuxtLink :to="`/invoices/${invoice.id}`" class="text-blue-600 hover:text-blue-900">
                        View<span class="sr-only">, {{ invoice.number }}</span>
                      </NuxtLink>
                    </td>
                  </tr>

                  <!-- Optional: empty state -->
                  <tr v-if="(invoices ?? []).length === 0">
                    <td colspan="7" class="py-6 text-center text-sm text-gray-500">
                      No invoices yet.
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

          </div>
        </div>
      </div>

    </div>
  </div>
</template>
