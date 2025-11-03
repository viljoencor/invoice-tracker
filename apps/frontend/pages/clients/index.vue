<script setup lang="ts">
definePageMeta({ middleware: 'auth' })

const { get } = useApi()
const list = ref<any[]>([])

onMounted(async () => {
  list.value = await get('/clients')
})
</script>

<template>
  <div class="p-6">
    <div class="flex items-center justify-between mb-4">
      <h1 class="text-2xl font-semibold">Clients</h1>
      <NuxtLink to="/clients/new" class="px-3 py-2 rounded bg-black text-white">New Client</NuxtLink>
    </div>
    <div class="overflow-x-auto bg-white rounded-2xl shadow">
      <table class="min-w-full">
        <thead>
          <tr class="text-left text-sm text-gray-500">
            <th class="p-3">Name</th>
            <th class="p-3">Email</th>
            <th class="p-3">Billing Address</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="c in list" :key="c.id" class="border-t">
            <td class="p-3">{{ c.name }}</td>
            <td class="p-3">{{ c.email }}</td>
            <td class="p-3">{{ c.billing_address }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>