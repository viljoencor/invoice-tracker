/**
 * Returns the private backend base URL.  Only callable from Nitro server code.
 * Defaults to the development FastAPI address when the env-var is absent.
 */
export function getBackendBase(): string {
  const config = useRuntimeConfig()
  const raw = (config.apiBase as string | undefined) || 'http://127.0.0.1:8000/api/v1'
  return raw.replace(/\/+$/, '')
}
