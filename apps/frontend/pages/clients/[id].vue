<script setup lang="ts">
import { ref, computed } from 'vue'
import { useForm, useField } from 'vee-validate'
import { toTypedSchema } from '@vee-validate/zod'
import { z } from 'zod'
import type { ClientOut } from '~/types/api'

definePageMeta({ middleware: 'auth' })

const route = useRoute()
const id = computed(() => String(route.params.id))
const api = useApi()

const { data: client, pending, error, refresh } = await useAsyncData<ClientOut | null>(
  () => `client-${id.value}`,
  () => api.get<ClientOut>(`/clients/${id.value}`),
  { default: (): ClientOut | null => null },
)

const editing = ref(false)
const saveError = ref<string | null>(null)
const saving = ref(false)

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

const { handleSubmit, errors, resetForm } = useForm({ validationSchema: clientSchema })
const { value: name } = useField<string>('name', undefined, { initialValue: '' })
const { value: email } = useField<string>('email', undefined, { initialValue: '' })
const { value: billing_address } = useField<string>('billing_address', undefined, { initialValue: '' })

function openEdit() {
  if (!client.value) return
  resetForm({
    values: {
      name: client.value.name,
      email: client.value.email ?? '',
      billing_address: client.value.billing_address ?? '',
    },
  })
  saveError.value = null
  editing.value = true
}

function cancelEdit() {
  editing.value = false
  saveError.value = null
}

const onSave = handleSubmit(async (values) => {
  saving.value = true
  saveError.value = null
  try {
    await api.patch(`/clients/${id.value}`, {
      name: values.name,
      email: values.email ?? null,
      billing_address: values.billing_address ?? null,
    })
    await refresh()
    editing.value = false
  } catch (e: any) {
    saveError.value = extractErrorMessage(e, 'Save failed. Please try again.')
  } finally {
    saving.value = false
  }
})

const confirmDelete = ref(false)
const deleting = ref(false)
const deleteError = ref<string | null>(null)

async function onDelete() {
  deleting.value = true
  deleteError.value = null
  try {
    await api.del(`/clients/${id.value}`)
    navigateTo('/clients')
  } catch (e: any) {
    const status = e?.status ?? e?.statusCode
    if (status === 409) {
      deleteError.value = 'This client has invoices and cannot be deleted.'
    } else if (status === 403 || status === 401) {
      deleteError.value = 'You do not have permission to delete this client.'
    } else if (status === 404) {
      deleteError.value = 'Client not found � it may have already been deleted.'
    } else {
      deleteError.value = extractErrorMessage(e, 'Delete failed. Please try again.')
    }
    confirmDelete.value = false
  } finally {
    deleting.value = false
  }
}
</script>

<template>
  <div class="p-6 space-y-6">
    <NuxtLink
      to="/clients"
      class="text-sm text-gray-500 hover:text-gray-900 focus:outline-none focus:ring-2 focus:ring-black rounded"
      data-testid="client-back"
    >&larr; Clients</NuxtLink>

    <div v-if="pending" class="text-sm text-gray-500" data-testid="client-loading" aria-live="polite">
      Loading&hellip;
    </div>

    <div v-else-if="error" class="bg-red-50 border border-red-200 rounded-2xl p-6 text-center" data-testid="client-load-error">
      <p class="text-sm text-red-700 mb-3">Failed to load client.</p>
      <button
        class="px-4 py-2 rounded bg-black text-white text-sm focus:outline-none focus:ring-2 focus:ring-black"
        data-testid="client-retry"
        @click="refresh()"
      >Retry</button>
    </div>

    <div v-else-if="!client" class="bg-yellow-50 border border-yellow-200 rounded-2xl p-6 text-center" data-testid="client-not-found">
      <p class="text-sm text-yellow-800">Client not found.</p>
    </div>

    <template v-else>
      <div class="flex items-start justify-between gap-4">
        <h1 class="text-2xl font-semibold" data-testid="client-name-heading">{{ client.name }}</h1>
        <div v-if="!editing" class="flex gap-2">
          <button
            class="px-3 py-2 text-sm rounded border border-gray-300 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-black"
            data-testid="client-edit-btn"
            @click="openEdit"
          >Edit</button>
          <button
            class="px-3 py-2 text-sm rounded bg-red-600 text-white hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-600"
            data-testid="client-delete-btn"
            @click="confirmDelete = true"
          >Delete</button>
        </div>
      </div>

      <div
        v-if="deleteError"
        class="bg-red-50 border border-red-200 rounded p-3 text-sm text-red-700"
        role="alert"
        data-testid="client-delete-error"
      >{{ deleteError }}</div>

      <div v-if="!editing" class="bg-white rounded-2xl shadow divide-y" data-testid="client-detail">
        <dl class="grid grid-cols-1 sm:grid-cols-3 gap-0">
          <div class="p-4 sm:border-r">
            <dt class="text-xs text-gray-500 uppercase tracking-wide">Name</dt>
            <dd class="mt-1 font-medium" data-testid="client-detail-name">{{ client.name }}</dd>
          </div>
          <div class="p-4 sm:border-r">
            <dt class="text-xs text-gray-500 uppercase tracking-wide">Email</dt>
            <dd class="mt-1" data-testid="client-detail-email">{{ client.email ?? '�' }}</dd>
          </div>
          <div class="p-4">
            <dt class="text-xs text-gray-500 uppercase tracking-wide">Billing Address</dt>
            <dd class="mt-1" data-testid="client-detail-address">{{ client.billing_address ?? '�' }}</dd>
          </div>
        </dl>
      </div>

      <form
        v-else
        class="bg-white rounded-2xl shadow p-6 space-y-5"
        data-testid="client-edit-form"
        @submit.prevent="onSave"
      >
        <h2 class="font-semibold text-lg">Edit Client</h2>
        <div
          v-if="saveError"
          class="bg-red-50 border border-red-200 rounded p-3 text-sm text-red-700"
          role="alert"
          data-testid="client-save-error"
        >{{ saveError }}</div>

        <div>
          <label for="edit-name" class="block text-sm font-medium text-gray-700">Name</label>
          <input
            id="edit-name"
            v-model="name"
            class="mt-1 w-full p-2 border rounded"
            :class="{ 'border-red-500': errors.name }"
            aria-describedby="edit-name-error"
          />
          <p v-if="errors.name" id="edit-name-error" class="mt-1 text-xs text-red-600" data-testid="client-edit-name-error">
            {{ errors.name }}
          </p>
        </div>

        <div>
          <label for="edit-email" class="block text-sm font-medium text-gray-700">Billing Email (optional)</label>
          <input
            id="edit-email"
            v-model="email"
            type="text"
            class="mt-1 w-full p-2 border rounded"
            :class="{ 'border-red-500': errors.email }"
            aria-describedby="edit-email-error"
          />
          <p v-if="errors.email" id="edit-email-error" class="mt-1 text-xs text-red-600" data-testid="client-edit-email-error">
            {{ errors.email }}
          </p>
        </div>

        <div>
          <label for="edit-address" class="block text-sm font-medium text-gray-700">Billing Address (optional)</label>
          <input id="edit-address" v-model="billing_address" class="mt-1 w-full p-2 border rounded" />
        </div>

        <div class="flex gap-3 pt-2">
          <button
            type="submit"
            :disabled="saving"
            class="px-4 py-2 rounded bg-black text-white disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-black"
            data-testid="client-save-btn"
          >{{ saving ? 'Saving�' : 'Save Changes' }}</button>
          <button
            type="button"
            class="px-4 py-2 rounded border border-gray-300 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-black"
            data-testid="client-cancel-btn"
            @click="cancelEdit"
          >Cancel</button>
        </div>
      </form>

      <div
        v-if="confirmDelete"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/40"
        role="dialog"
        aria-modal="true"
        aria-labelledby="confirm-delete-title"
        data-testid="delete-confirm-dialog"
      >
        <div class="bg-white rounded-2xl shadow-xl p-6 max-w-sm w-full mx-4 space-y-4">
          <h2 id="confirm-delete-title" class="text-lg font-semibold">Delete client?</h2>
          <p class="text-sm text-gray-600">
            This will permanently delete <strong>{{ client.name }}</strong>. This action cannot be undone.
          </p>
          <div class="flex gap-3 justify-end">
            <button
              class="px-4 py-2 rounded border border-gray-300 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-black"
              data-testid="delete-cancel-btn"
              :disabled="deleting"
              @click="confirmDelete = false"
            >Cancel</button>
            <button
              class="px-4 py-2 rounded bg-red-600 text-white hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-600 disabled:opacity-50"
              data-testid="delete-confirm-btn"
              :disabled="deleting"
              @click="onDelete"
            >{{ deleting ? 'Deleting�' : 'Yes, delete' }}</button>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>