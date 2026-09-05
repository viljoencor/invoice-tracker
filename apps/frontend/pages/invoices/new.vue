<script setup lang="ts">
import { computed, ref, reactive, onMounted, watch } from 'vue'
import { z } from 'zod'
import type { ClientOut } from '~/types/api'

definePageMeta({ middleware: 'auth' })

const { get, post } = useApi()

type LineItem = {
  description: string
  qty: number
  unit_price_cents: number
  tax_rate_bp: number
}

const clients = ref<ClientOut[]>([])
const form = reactive<{
  client_id: string
  issue_date: string
  due_date: string
  currency: string
  notes: string
  items: LineItem[]
}>({
  client_id: '',
  issue_date: new Date().toISOString().slice(0,10),
  due_date: new Date(Date.now() + 1000*60*60*24*30).toISOString().slice(0,10),
  currency: 'ZAR',
  notes: '',
  items: [{ description: 'Service', qty: 1, unit_price_cents: 10000, tax_rate_bp: 1500 }]
})

const activeClients = computed(() => clients.value)

onMounted(async () => {
  clients.value = await get<ClientOut[]>('/clients')
  form.client_id = clients.value[0]?.id ?? ''
})

const addItem = () => {
  form.items.push({ description: '', qty: 1, unit_price_cents: 0, tax_rate_bp: 0 })
}
const removeItem = (idx: number) => {
  form.items.splice(idx, 1)
}

const formatCurrency = (cents: number) =>
  new Intl.NumberFormat('en-ZA', { style: 'currency', currency: form.currency || 'ZAR' }).format((cents || 0) / 100)

const totals = computed(() => {
  let subtotal = 0
  let tax = 0
  for (const it of form.items) {
    const line = Number(it.qty || 0) * Number(it.unit_price_cents || 0)
    const lineTax = line * (Number(it.tax_rate_bp || 0) / 10000)
    subtotal += Math.round(line)
    tax += Math.round(lineTax)
  }
  return {
    subtotal_cents: subtotal,
    tax_cents: tax,
    total_cents: subtotal + tax,
  }
})

const canSubmit = computed(() =>
  !!form.client_id &&
  !!form.issue_date &&
  !!form.due_date &&
  form.items.length > 0 &&
  form.items.every(i => i.description.trim().length > 0 && i.qty > 0 && i.unit_price_cents >= 0 && i.tax_rate_bp >= 0)
)

// ── Zod validation ────────────────────────────────────────────────────────────
const invoiceSchema = z
  .object({
    client_id: z.string().min(1, 'Client is required'),
    issue_date: z.string().min(1, 'Issue date is required'),
    due_date: z.string().min(1, 'Due date is required'),
    items: z
      .array(
        z.object({
          description: z.string().min(1, 'Description is required'),
          qty: z.number().positive('Quantity must be positive'),
          unit_price_cents: z.number().nonnegative('Unit price cannot be negative'),
          tax_rate_bp: z.number().nonnegative('Tax rate cannot be negative'),
        }),
      )
      .min(1, 'At least one line item is required'),
  })
  .refine((data) => data.due_date >= data.issue_date, {
    message: 'Due date cannot be before issue date',
    path: ['due_date'],
  })

const formErrors = ref<Record<string, string>>({})
const submitting = ref(false)
const submitError = ref<string | null>(null)

async function submit() {
  formErrors.value = {}
  submitError.value = null
  const result = invoiceSchema.safeParse(form)
  if (!result.success) {
    const errs: Record<string, string> = {}
    for (const issue of result.error.issues) {
      const key = issue.path.join('.')
      if (!errs[key]) errs[key] = issue.message
    }
    formErrors.value = errs
    return
  }
  submitting.value = true
  try {
    // Idempotency-Key protects against double-submit / network-retry duplicate invoices,
    // mirroring the payment-recording pattern.
    const idem = crypto.randomUUID()
    const inv = await post<{ id: string }>('/invoices', form, {
      headers: { 'Idempotency-Key': idem },
    })
    navigateTo(`/invoices/${inv.id}`)
  } catch (e: any) {
    submitError.value = extractErrorMessage(e, 'Failed to create invoice')
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="p-6 space-y-6">
    <h1 class="text-2xl font-semibold">New Invoice</h1>

    <div class="bg-white p-5 rounded-2xl shadow space-y-6">
      <!-- Client & Dates -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <label for="client" class="block text-sm font-medium text-gray-700">Client</label>
          <select
            id="client"
            v-model="form.client_id"
            class="mt-1 w-full p-2 border rounded"
            aria-describedby="client-hint"
          >
            <option v-for="c in activeClients" :key="c.id" :value="c.id">{{ c.name }}</option>
          </select>
          <p id="client-hint" class="mt-1 text-xs text-gray-500">
            Choose who you’re billing.
          </p>
        </div>

        <div>
          <label for="issue_date" class="block text-sm font-medium text-gray-700">Issue Date</label>
          <input
            id="issue_date"
            v-model="form.issue_date"
            type="date"
            class="mt-1 w-full p-2 border rounded"
            aria-describedby="issue-hint"
          />
          <p id="issue-hint" class="mt-1 text-xs text-gray-500">
            The date the invoice is created and sent.
          </p>
        </div>

        <div>
          <label for="due_date" class="block text-sm font-medium text-gray-700">Due Date</label>
          <input
            id="due_date"
            v-model="form.due_date"
            type="date"
            class="mt-1 w-full p-2 border rounded"
            :class="{ 'border-red-500': formErrors['due_date'] }"
            aria-describedby="due-hint due-date-error"
          />
          <p v-if="formErrors['due_date']" id="due-date-error" class="mt-1 text-xs text-red-600" data-testid="due-date-error">
            {{ formErrors['due_date'] }}
          </p>
          <p v-else id="due-hint" class="mt-1 text-xs text-gray-500">
            Payment is expected on or before this date.
          </p>
        </div>
      </div>

      <!-- Notes -->
      <div>
        <label for="notes" class="block text-sm font-medium text-gray-700">Notes (optional)</label>
        <textarea
          id="notes"
          v-model="form.notes"
          class="mt-1 w-full p-2 border rounded"
          placeholder="e.g. Payment via EFT within 30 days"
          rows="3"
        />
        <p class="mt-1 text-xs text-gray-500">
          Displayed on the invoice under “Notes”.
        </p>
      </div>

      <!-- Line Items -->
      <div>
        <div class="flex items-center justify-between mb-2">
          <h2 class="text-sm font-semibold text-gray-700">Line Items</h2>
          <button
            type="button"
            class="text-sm px-3 py-1 rounded border border-gray-300 hover:bg-gray-50"
            @click="addItem"
          >
            + Add item
          </button>
        </div>

        <div class="hidden md:grid grid-cols-12 gap-2 text-xs text-gray-500 px-1 py-2">
          <div class="col-span-6">Description</div>
          <div class="col-span-2 text-right">Qty</div>
          <div class="col-span-2 text-right">Unit (cents)</div>
          <div class="col-span-1 text-right">Tax (bp)</div>
          <div class="col-span-1"></div>
        </div>

        <div
          v-for="(it, idx) in form.items"
          :key="idx"
          class="grid grid-cols-1 md:grid-cols-12 gap-2 items-center mb-2"
        >
          <input
            v-model="it.description"
            class="md:col-span-6 p-2 border rounded"
            placeholder="Description (e.g. Development, Consulting, Support)"
            :aria-label="`Item ${idx+1} description`"
          />
          <input
            v-model.number="it.qty"
            type="number"
            step="0.01"
            min="0"
            class="md:col-span-2 p-2 border rounded text-right"
            placeholder="1"
            :aria-label="`Item ${idx+1} quantity`"
          />
          <input
            v-model.number="it.unit_price_cents"
            type="number"
            min="0"
            class="md:col-span-2 p-2 border rounded text-right"
            placeholder="10000"
            :aria-label="`Item ${idx+1} unit price (cents)`"
          />
          <input
            v-model.number="it.tax_rate_bp"
            type="number"
            min="0"
            class="md:col-span-1 p-2 border rounded text-right"
            placeholder="1500"
            :aria-label="`Item ${idx+1} tax basis points`"
          />
          <div class="md:col-span-1 flex justify-end">
            <button
              v-if="form.items.length > 1"
              type="button"
              class="text-xs px-2 py-1 rounded border border-gray-300 hover:bg-gray-50"
              @click="removeItem(idx)"
              :aria-label="`Remove item ${idx+1}`"
            >
              Remove
            </button>
          </div>

          <!-- Inline helper for mobile -->
          <div class="md:hidden text-[11px] text-gray-500 -mt-1">
            Tip: “Unit (cents)” = Rands × 100. e.g. R 100.00 → 10000
          </div>
        </div>

        <p class="hidden md:block text-xs text-gray-500 mt-1">
          Tip: “Unit (cents)” = amount in cents (Rands × 100). Example: R 100.00 → <b>10000</b>.
        </p>
      </div>

      <!-- Totals -->
      <div class="border-t pt-4 grid grid-cols-1 md:grid-cols-3 gap-4">
        <div class="md:col-span-2"></div>
        <div class="bg-gray-50 rounded-lg p-3 space-y-1">
          <div class="flex items-center justify-between text-sm">
            <span class="text-gray-600">Subtotal</span>
            <span class="font-medium">{{ formatCurrency(totals.subtotal_cents) }}</span>
          </div>
          <div class="flex items-center justify-between text-sm">
            <span class="text-gray-600">Tax</span>
            <span class="font-medium">{{ formatCurrency(totals.tax_cents) }}</span>
          </div>
          <div class="flex items-center justify-between text-base pt-1 border-t mt-2">
            <span class="font-semibold">Total</span>
            <span class="font-semibold">{{ formatCurrency(totals.total_cents) }}</span>
          </div>
        </div>
      </div>

      <!-- Actions -->
      <div class="flex items-center gap-3 pt-2">
        <button
          type="button"
          @click="submit"
          :disabled="submitting || !canSubmit"
          class="px-4 py-2 rounded bg-black text-white disabled:opacity-50"
          data-testid="invoice-submit"
        >
          {{ submitting ? 'Creating…' : 'Create Invoice' }}
        </button>
        <span v-if="submitError" class="text-xs text-red-600" data-testid="submit-error">{{ submitError }}</span>
        <span v-else-if="formErrors['items']" class="text-xs text-red-600" data-testid="items-error">{{ formErrors['items'] }}</span>
        <span v-else-if="!canSubmit" class="text-xs text-gray-500">
          Complete required fields to enable “Create Invoice”.
        </span>
      </div>
    </div>
  </div>
</template>
