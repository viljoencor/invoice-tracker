// apps/frontend/composables/useApiError.ts
// Centralises the repeated `e?.data?.detail ?? e?.message ?? fallback` extraction
// pattern that was previously duplicated across several pages' catch blocks.
export function extractErrorMessage(e: unknown, fallback: string): string {
  const detail = (e as { data?: { detail?: unknown } } | undefined)?.data?.detail
  if (typeof detail === 'string') return detail
  const message = (e as { message?: unknown } | undefined)?.message
  if (typeof message === 'string' && message) return message
  return fallback
}

export function useApiError() {
  return { extractErrorMessage }
}
