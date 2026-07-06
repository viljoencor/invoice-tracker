<script setup lang="ts">
import type { ClientOut } from '~/types/api'

definePageMeta({ middleware: 'auth' })

const api = useApi()

const { data: clients, pending, error, refresh } = await useAsyncData<ClientOut[]>(
  'clients',
  () => api.get<ClientOut[]>('/clients'),
  { default: (): ClientOut[] => [] },
)
</script>

<template>
  <div class="p-6">
    <div class="flex items-center justify-between mb-4">
      <h1 class="text-2xl font-semibold">Clients</h1>
      <NuxtLink to="/clients/new" class="px-3 py-2 rounded bg-black text-white focus:outline-none focus:ring-2 focus:ring-black">
        New Client
      </NuxtLink>
    </div>

    <!-- Loading -->
    <div v-if="pending" class="text-sm text-gray-500" data-testid="clients-loading" aria-live="polite">
      Loading clients…
    </div>

    <!-- Error + retry -->
    <div v-else-if="error" class="bg-red-50 border border-red-200 rounded-2xl p-6 text-center" data-testid="clients-error">
      <p class="text-sm text-red-700 mb-3">Failed to load clients. Please try again.</p>
      <button
        class="px-4 py-2 rounded bg-black text-white text-sm focus:outline-none focus:ring-2 focus:ring-black"
        data-testid="clients-retry"
        @click="refresh()"
      >
        Retry
      </button>
    </div>

    <!-- Empty state -->
    <div
      v-else-if="(clients ?? []).length === 0"
      class="bg-white rounded-2xl shadow p-10 text-center text-gray-500"
      data-testid="clients-empty"
    >
      <p class="mb-3">No clients yet.</p>
      <NuxtLink to="/clients/new" class="text-sm underline">Add your first client →</NuxtLink>
    </div>

    <!-- Table -->
    <div v-else class="overflow-x-auto bg-white rounded-2xl shadow" data-testid="clients-table">
      <table class="min-w-full">
        <thead>
          <tr class="text-left text-sm text-gray-500">
            <th class="p-3">Name</th>
            <th class="p-3">Email</th>
            <th class="p-3">Billing Address</th>
            <th class="p-3 sr-only">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="c in clients"
            :key="c.id"
            class="border-t hover:bg-gray-50"
          >
            <td class="p-3">
              <NuxtLink
                :to="`/clients/${c.id}`"
                class="font-medium hover:underline focus:outline-none focus:ring-2 focus:ring-black rounded"
                :data-testid="`client-row-${c.id}`"
              >
                {{ c.name }}
              </NuxtLink>
            </td>
            <td class="p-3 text-gray-600">{{ c.email ?? '—' }}</td>
            <td class="p-3 text-gray-600">{{ c.billing_address ?? '—' }}</td>
            <td class="p-3">
              <NuxtLink
                :to="`/clients/${c.id}`"
                class="text-sm text-gray-500 hover:text-gray-900 focus:outline-none focus:ring-2 focus:ring-black rounded"
              >
                View →
              </NuxtLink>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>