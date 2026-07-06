import { defineConfig, devices } from '@playwright/test'

/**
 * Playwright E2E configuration.
 *
 * Prerequisites: the full stack must be running.
 *   docker compose up -d
 *
 * Configuration env vars:
 *   E2E_BASE_URL      Frontend URL   (default: http://localhost:3000)
 *   E2E_TEST_EMAIL    Test user email (default: admin@example.com)
 *   E2E_TEST_PASSWORD Test user password — must be provided via env, no default
 */
export default defineConfig({
  testDir: './tests/e2e',
  timeout: 30_000,
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI
    ? [['github'], ['html', { outputFolder: 'playwright-report', open: 'never' }]]
    : [['list']],
  use: {
    baseURL: process.env.E2E_BASE_URL ?? 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
})
