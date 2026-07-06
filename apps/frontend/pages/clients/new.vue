<script setup lang="ts">
import { useForm, useField } from 'vee-validate'
import { toTypedSchema } from '@vee-validate/zod'
import { z } from 'zod'

definePageMeta({ middleware: 'auth' })

const { post } = useApi()

const clientSchema = toTypedSchema(
  z.object({
    name: z.string().min(1, 'Client name is required'),
    email: z
      .union([z.string().email('Invalid email format'), z.literal('')])
      .optional()
      .transform((v) => v || null),
    billing_address: z.string().optional().transform((v) => v || null),
  }),
)

const { handleSubmit, errors, isSubmitting } = useForm({ validationSchema: clientSchema })
const { value: name } = useField<string>('name', undefined, { initialValue: '' })
const { value: email } = useField<string>('email', undefined, { initialValue: '' })
const { value: billing_address } = useField<string>('billing_address', undefined, { initialValue: '' })

const onCreate = handleSubmit(async (values) => {
  await post('/clients', {
    name: values.name,
    email: values.email ?? null,
    billing_address: values.billing_address ?? null,
  })
  navigateTo('/clients')
})
</script>

<template>
  <div class="p-6 space-y-6">
    <h1 class="text-2xl font-semibold">New Client</h1>

    <form class="bg-white p-5 rounded-2xl shadow space-y-5" @submit.prevent="onCreate">
      <div>
        <label for="client-name" class="block text-sm font-medium text-gray-700">
          Client Name
        </label>
        <input
          id="client-name"
          v-model="name"
          placeholder="e.g. Acme Pty Ltd"
          class="mt-1 w-full p-2 border rounded"
          :class="{ 'border-red-500': errors.name }"
          aria-describedby="name-hint name-error"
        />
        <p v-if="errors.name" id="name-error" class="mt-1 text-xs text-red-600" data-testid="name-error">
          {{ errors.name }}
        </p>
        <p v-else id="name-hint" class="mt-1 text-xs text-gray-500">
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
          type="text"
          placeholder="billing@company.co.za"
          class="mt-1 w-full p-2 border rounded"
          :class="{ 'border-red-500': errors.email }"
          aria-describedby="email-hint email-error"
        />
        <p v-if="errors.email" id="email-error" class="mt-1 text-xs text-red-600" data-testid="email-error">
          {{ errors.email }}
        </p>
        <p v-else id="email-hint" class="mt-1 text-xs text-gray-500">
          Where you'll send invoices and statements.
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
          type="submit"
          :disabled="isSubmitting"
          class="px-4 py-2 rounded bg-black text-white disabled:opacity-50"
          data-testid="client-submit"
        >
          Create Client
        </button>
      </div>
    </form>
  </div>
</template>