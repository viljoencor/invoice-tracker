/**
 * Business-flow E2E smoke tests — clients, invoices, and payments.
 *
 * Closes the gap where only the login flow had E2E coverage: this suite
 * exercises the primary happy path across all three core domains in one
 * user journey (create client -> create invoice -> send -> record payment).
 *
 * PREREQUISITES — same as auth.spec.ts: the full stack must be running and
 * seeded (docker compose up -d; python -m app.scripts.seed).
 *
 * CONFIGURATION (environment variables):
 *   E2E_BASE_URL      The base URL of the running frontend  (default: http://localhost:3000)
 *   E2E_TEST_EMAIL    Email of a seeded test account        (default: admin@example.com)
 *   E2E_TEST_PASSWORD Password for the test account — no default; must be set
 *
 * Run:
 *   npm run test:e2e
 *
 * The whole suite is skipped when E2E_TEST_PASSWORD is not set, matching the
 * convention already used for the "valid credentials" test in auth.spec.ts.
 */
import { test, expect } from '@playwright/test'

const email = process.env.E2E_TEST_EMAIL ?? 'admin@example.com'
const password = process.env.E2E_TEST_PASSWORD ?? ''

test.describe('Client -> Invoice -> Payment happy path', () => {
  test.skip(!password, 'E2E_TEST_PASSWORD not set — skipping business-flow E2E tests')

  test.beforeEach(async ({ page }) => {
    await page.goto('/login')
    await page.getByTestId('login-email').fill(email)
    await page.getByTestId('login-password').fill(password)
    await page.getByTestId('login-submit').click()
    await expect(page).toHaveURL(/\/(dashboard)?$/)
  })

  test('creates a client, invoices it, sends the invoice, and records a payment', async ({ page }) => {
    const uniqueSuffix = Date.now()
    const clientName = `E2E Test Client ${uniqueSuffix}`

    // ── 1. Create a client ──────────────────────────────────────────────
    await page.goto('/clients/new')
    await page.locator('#client-name').fill(clientName)
    await page.locator('#client-email').fill(`e2e-${uniqueSuffix}@example.com`)
    await page.getByTestId('client-submit').click()
    await expect(page).toHaveURL(/\/clients$/)

    await expect(page.getByTestId('clients-table')).toContainText(clientName)

    // ── 2. Create an invoice for that client ────────────────────────────
    await page.goto('/invoices/new')
    await page.locator('#client').selectOption({ label: clientName })
    await page.locator('#issue_date').fill(new Date().toISOString().slice(0, 10))
    const due = new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().slice(0, 10)
    await page.locator('#due_date').fill(due)
    await page.getByTestId('invoice-submit').click()

    await expect(page).toHaveURL(/\/invoices\/[0-9a-f-]+$/)
    await expect(page.getByText(/Invoice INV-/)).toBeVisible()

    // ── 3. Mark the invoice as sent ──────────────────────────────────────
    const sendButton = page.getByTestId('send-invoice-btn')
    if (await sendButton.isVisible()) {
      await sendButton.click()
      await expect(sendButton).not.toBeVisible()
    }

    // ── 4. Record a partial payment ─────────────────────────────────────
    await page.locator('input[placeholder="e.g. 115.00"]').fill('50.00')
    await page.getByTestId('save-payment-btn').click()

    await expect(page.getByTestId('pay-error')).not.toBeVisible()
    await expect(page.getByText(/partially_paid|paid/i)).toBeVisible()
  })
})
