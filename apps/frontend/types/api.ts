/**
 * Shared TypeScript types that mirror the FastAPI backend schemas.
 * Keep these in sync with apps/backend/app/schemas.py and the actual router responses.
 */

// ── Auth ─────────────────────────────────────────────────────────────────────
export interface TokenResponse {
  access_token: string
  token_type: 'bearer'
}

export interface UserOut {
  id: string
  email: string
  name: string
  org_id: string
  role: string
}

// ── Clients ───────────────────────────────────────────────────────────────────
export interface ClientOut {
  id: string
  name: string
  email: string | null
  billing_address: string | null
}

export interface ClientIn {
  name: string
  email?: string | null
  billing_address?: string | null
}

// ── Invoice line item ─────────────────────────────────────────────────────────
export interface InvoiceItemIn {
  description: string
  qty: number
  unit_price_cents: number
  tax_rate_bp: number
}

// ── Invoice create request ────────────────────────────────────────────────────
export interface InvoiceCreate {
  client_id: string
  issue_date: string
  due_date: string
  currency?: string
  notes?: string | null
  items: InvoiceItemIn[]
}

// ── Invoice list row — matches GET /invoices ──────────────────────────────────
export interface InvoiceList {
  id: string
  number: string
  client_name: string
  issue_date: string
  due_date: string
  total_cents: number
  balance_cents: number
  status: string
  currency: string
}

// ── Invoice detail — matches GET /invoices/:id ────────────────────────────────
export interface InvoiceDetail extends InvoiceList {
  client_id: string
  subtotal_cents: number
  tax_cents: number
  notes: string | null
}

// ── Payment ───────────────────────────────────────────────────────────────────
export interface PaymentOut {
  id: string
  amount_cents: number
  received_at: string
  method: string | null
  reference: string | null
}

// ── Dashboard — matches the actual GET /dash/summary response ─────────────────
export interface RevenueMonth {
  month: string      // "YYYY-MM"
  total_cents: number
  count: number
}

export interface DashboardSummary {
  total_billed_cents: number
  total_due_cents: number
  overdue_count: number
  pending_count: number
  bkt_0_30: number | null
  bkt_31_60: number | null
  bkt_61_90: number | null
  bkt_90p: number | null
  revenue_by_month: RevenueMonth[]
}

// ── API error ─────────────────────────────────────────────────────────────────
export interface ApiErrorDetail {
  message?: string
  code?: string
}

export interface ApiError {
  detail: string | ApiErrorDetail | Record<string, unknown>
}
