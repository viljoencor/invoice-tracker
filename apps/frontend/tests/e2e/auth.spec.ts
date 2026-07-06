/**
 * Authentication E2E smoke tests.
 *
 * PREREQUISITES — these tests require the full stack to be running:
 *   docker compose up -d
 *   (starts PostgreSQL, the FastAPI backend, and the Nuxt frontend)
 *
 * The database must be seeded with at least one user account.
 * Use the seed script:  docker compose exec backend python scripts/seed.py
 *
 * CONFIGURATION (environment variables):
 *   E2E_BASE_URL      The base URL of the running frontend  (default: http://localhost:3000)
 *   E2E_TEST_EMAIL    Email of a seeded test account        (default: admin@example.com)
 *   E2E_TEST_PASSWORD Password for the test account — no default; must be set
 *
 * Run:
 *   npm run test:e2e
 *
 * Do NOT hard-code credentials in this file; always supply them via env vars.
 */
import { test, expect } from '@playwright/test'

const email = process.env.E2E_TEST_EMAIL ?? 'admin@example.com'
const password = process.env.E2E_TEST_PASSWORD ?? ''

test.describe('Authentication flow', () => {
  test('unauthenticated visit to / redirects to /login', async ({ page }) => {
    // Clear any stored session
    await page.context().clearCookies()
    await page.goto('/')
    await expect(page).toHaveURL(/\/login/)
  })

  test('login page renders the sign-in form', async ({ page }) => {
    await page.goto('/login')
    await expect(page.getByTestId('login-email')).toBeVisible()
    await expect(page.getByTestId('login-password')).toBeVisible()
    await expect(page.getByTestId('login-submit')).toBeVisible()
  })

  test('invalid credentials show an error message', async ({ page }) => {
    await page.goto('/login')
    await page.getByTestId('login-email').fill(email || 'user@example.com')
    await page.getByTestId('login-password').fill('definitely-wrong-password-xyz')
    await page.getByTestId('login-submit').click()
    await expect(page.getByTestId('login-error')).toBeVisible()
  })

  test('valid credentials navigate to the dashboard', async ({ page }) => {
    test.skip(!password, 'E2E_TEST_PASSWORD not set — skipping valid-login test')

    await page.goto('/login')
    await page.getByTestId('login-email').fill(email)
    await page.getByTestId('login-password').fill(password)
    await page.getByTestId('login-submit').click()

    // After login the app navigates to /dashboard which then redirects to /
    await expect(page).toHaveURL(/\/(dashboard)?$/)
  })
})
