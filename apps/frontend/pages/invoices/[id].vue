<script setup lang="ts">
definePageMeta({ middleware: 'auth' })

const route = useRoute()
const id = computed(() => String(route.params.id))
const api = useApi()

// include refresh so we can re-fetch after a payment
const { data, pending, error, refresh } = await useAsyncData(
  () => `invoice-${id.value}`,
  () => api.get(`/invoices/${id.value}`),
  { default: () => null }
)

const invoice = computed<any | null>(() => data.value ?? null)

const formatCurrency = (cents: number) =>
  new Intl.NumberFormat('en-ZA', { style: 'currency', currency: 'ZAR' }).format((cents ?? 0) / 100)

const formatDate = (d?: string) =>
  d ? new Date(d).toLocaleDateString('en-ZA', { year: 'numeric', month: 'short', day: 'numeric' }) : ''

// ---------- PDF ----------
const downloading = ref(false)
const downloadPdf = async () => {
  try {
    downloading.value = true
    const bytes = await api.getArrayBuffer(`/invoices/${id.value}/pdf`)
    const blob = new Blob([bytes as ArrayBuffer], { type: 'application/pdf' })
    const url = URL.createObjectURL(blob)
    window.open(url, '_blank')
    setTimeout(() => URL.revokeObjectURL(url), 60_000)
  } finally {
    downloading.value = false
  }
}

// ---------- Record Payment ----------
const paying = ref(false)
const pay = reactive({
  amount_rands: '' as string,
  received_at: new Date().toISOString().slice(0, 10),
  method: 'EFT',
  reference: ''
})

const payError = ref<string | null>(null)
async function recordPayment() {
  payError.value = null
  try {
    paying.value = true

    // Convert rand string -> cents integer safely
    const rands = Number((pay.amount_rands || '').toString().replace(',', '.'))
    if (!isFinite(rands) || rands <= 0) {
      payError.value = 'Please enter a valid amount in rands (e.g. 115.00).'
      return
    }
    const amount_cents = Math.round(rands * 100)

    // quick guard against overpay
    const currentBalance = Number(invoice.value?.balance_cents ?? 0)
    if (amount_cents > currentBalance) {
      payError.value = `Amount exceeds current balance (${formatCurrency(currentBalance)}).`
      return
    }

    const idem = crypto.randomUUID()
    await api.post(
      '/payments',
      {
        invoice_id: id.value,
        amount_cents,
        received_at: pay.received_at,
        method: pay.method || null,
        reference: pay.reference || null
      },
      { headers: { 'Idempotency-Key': idem } }
    )

    // reset amount field; refresh invoice details
    pay.amount_rands = ''
    await refresh()
  } catch (e: any) {
    // surface backend error message if available
    const msg = e?.data?.detail || e?.message || 'Payment failed'
    payError.value = String(msg)
  } finally {
    paying.value = false
  }
}

// ---------- (Optional) fetch payments list to show history ----------
const { data: paymentsData, refresh: refreshPayments } = await useAsyncData(
  () => `payments-${id.value}`,
  () => api.get('/payments', { params: { invoice_id: id.value } }),
  { default: () => [] }
)
watch(data, () => refreshPayments()) // refresh payments when invoice refetches
const payments = computed<any[]>(() => paymentsData.value || [])
</script>

<template>
  <div class="p-6 space-y-6">
    <div v-if="pending" class="text-sm text-gray-500">Loading…</div>
    <div v-else-if="error" class="text-sm text-red-600">Failed to load invoice</div>

    <div v-else-if="invoice" class="space-y-6">
      <div class="flex items-center justify-between">
        <h1 class="text-2xl font-semibold">Invoice {{ invoice.number }}</h1>
        <button
          @click="downloadPdf"
          :disabled="downloading"
          class="px-3 py-2 rounded bg-black text-white disabled:opacity-60"
        >
          {{ downloading ? 'Preparing…' : 'Download PDF' }}
        </button>
      </div>

      <!-- Details -->
      <div class="bg-white p-4 rounded-2xl shadow">
        <dl class="grid grid-cols-2 gap-x-6 gap-y-3">
          <div>
            <dt class="text-sm text-gray-500">Client</dt>
            <dd class="text-sm text-gray-900">{{ invoice.client_name || invoice.client_id }}</dd>
          </div>
          <div>
            <dt class="text-sm text-gray-500">Status</dt>
            <dd class="text-sm text-gray-900 capitalize">{{ invoice.status }}</dd>
          </div>

          <div>
            <dt class="text-sm text-gray-500">Issue</dt>
            <dd class="text-sm text-gray-900">{{ formatDate(invoice.issue_date) }}</dd>
          </div>
          <div>
            <dt class="text-sm text-gray-500">Due</dt>
            <dd class="text-sm text-gray-900">{{ formatDate(invoice.due_date) }}</dd>
          </div>

          <div>
            <dt class="text-sm text-gray-500">Subtotal</dt>
            <dd class="text-sm text-gray-900">{{ formatCurrency(invoice.subtotal_cents) }}</dd>
          </div>
          <div>
            <dt class="text-sm text-gray-500">Tax</dt>
            <dd class="text-sm text-gray-900">{{ formatCurrency(invoice.tax_cents) }}</dd>
          </div>
          <div>
            <dt class="text-sm text-gray-500">Total</dt>
            <dd class="text-sm text-gray-900 font-medium">{{ formatCurrency(invoice.total_cents) }}</dd>
          </div>
          <div>
            <dt class="text-sm text-gray-500">Balance</dt>
            <dd class="text-sm text-gray-900 font-medium">{{ formatCurrency(invoice.balance_cents) }}</dd>
          </div>
        </dl>
      </div>

      <!-- Record Payment -->
      <div class="bg-white p-4 rounded-2xl shadow space-y-3">
        <h2 class="text-lg font-semibold">Record Payment</h2>

        <div v-if="payError" class="text-sm text-red-600">{{ payError }}</div>

        <div class="grid grid-cols-1 md:grid-cols-4 gap-3">
          <div>
            <label class="block text-sm text-gray-600 mb-1">Amount (ZAR)</label>
            <input
              v-model="pay.amount_rands"
              type="number"
              step="0.01"
              min="0"
              class="w-full p-2 border rounded"
              placeholder="e.g. 115.00"
            />
          </div>
          <div>
            <label class="block text-sm text-gray-600 mb-1">Received At</label>
            <input v-model="pay.received_at" type="date" class="w-full p-2 border rounded" />
          </div>
          <div>
            <label class="block text-sm text-gray-600 mb-1">Method</label>
            <input v-model="pay.method" class="w-full p-2 border rounded" placeholder="EFT / Card / Cash" />
          </div>
          <div>
            <label class="block text-sm text-gray-600 mb-1">Reference</label>
            <input v-model="pay.reference" class="w-full p-2 border rounded" placeholder="Reference" />
          </div>
        </div>

        <div class="pt-2">
          <button
            @click="recordPayment"
            :disabled="paying"
            class="px-3 py-2 rounded bg-blue-600 text-white disabled:opacity-60"
          >
            {{ paying ? 'Saving…' : 'Save Payment' }}
          </button>
        </div>
      </div>

      <!-- Payments History (optional) -->
      <div class="bg-white p-4 rounded-2xl shadow" v-if="payments.length">
        <h2 class="text-lg font-semibold mb-2">Payments</h2>
        <ul class="divide-y">
          <li v-for="p in payments" :key="p.id" class="py-2 flex items-center justify-between">
            <div class="text-sm text-gray-700">
              {{ p.received_at }} · {{ p.method || '—' }} · {{ p.reference || '' }}
            </div>
            <div class="text-sm font-medium">
              {{ formatCurrency(p.amount_cents) }}
            </div>
          </li>
        </ul>
      </div>
    </div>

    <div v-else class="text-sm text-gray-500">Not found</div>
  </div>
</template>
