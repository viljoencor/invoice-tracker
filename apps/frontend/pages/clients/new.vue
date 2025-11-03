<script setup lang="ts">
definePageMeta({ middleware: 'auth' })

const { post } = useApi()

const name = ref('')
const email = ref('')
const billing_address = ref('')

const canCreate = computed(() => name.value.trim().length > 0)

async function create() {
  await post('/clients', {
    name: name.value,
    email: email.value || null,
    billing_address: billing_address.value || null
  })
  navigateTo('/clients')
}
</script>

<template>
  <div class="p-6 space-y-6">
    <h1 class="text-2xl font-semibold">New Client</h1>

    <div class="bg-white p-5 rounded-2xl shadow space-y-5">
      <div>
        <label for="client-name" class="block text-sm font-medium text-gray-700">
          Client Name
        </label>
        <input
          id="client-name"
          v-model="name"
          placeholder="e.g. Acme Pty Ltd"
          class="mt-1 w-full p-2 border rounded"
          aria-describedby="name-hint"
        />
        <p id="name-hint" class="mt-1 text-xs text-gray-500">
          The legal or trading name that will appear on invoices.
        </p>
      </div>

      <div>
        <label for="client-email" class="block text-sm font-medium text-gray-700">
          Billing Email (optional)
        </label>
        <input
          id="client-email"
          v-model="email"
          type="email"
          placeholder="billing@company.co.za"
          class="mt-1 w-full p-2 border rounded"
          aria-describedby="email-hint"
        />
        <p id="email-hint" class="mt-1 text-xs text-gray-500">
          Where you’ll send invoices and statements.
        </p>
      </div>

      <div>
        <label for="client-address" class="block text-sm font-medium text-gray-700">
          Billing Address (optional)
        </label>
        <input
          id="client-address"
          v-model="billing_address"
          placeholder="Street, City, Post Code"
          class="mt-1 w-full p-2 border rounded"
          aria-describedby="addr-hint"
        />
        <p id="addr-hint" class="mt-1 text-xs text-gray-500">
          Appears on invoices if provided.
        </p>
      </div>

      <div class="pt-2">
        <button
          @click="create"
          :disabled="!canCreate"
          class="px-4 py-2 rounded bg-black text-white disabled:opacity-50"
        >
          Create Client
        </button>
        <span v-if="!canCreate" class="ml-2 text-xs text-gray-500">
          Enter at least a client name.
        </span>
      </div>
    </div>
  </div>
</template>
