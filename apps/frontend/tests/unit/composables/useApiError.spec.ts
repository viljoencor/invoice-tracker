import { describe, it, expect } from 'vitest'
import { extractErrorMessage } from '../../../composables/useApiError'

describe('extractErrorMessage', () => {
  it('prefers a string detail field from an ofetch-style error', () => {
    expect(extractErrorMessage({ data: { detail: 'Invalid credentials' } }, 'fallback')).toBe(
      'Invalid credentials',
    )
  })

  it('falls back to the error message when detail is not a string', () => {
    expect(
      extractErrorMessage({ data: { detail: { code: 'x' } }, message: 'Request failed' }, 'fallback'),
    ).toBe('Request failed')
  })

  it('falls back to the provided default when nothing usable is present', () => {
    expect(extractErrorMessage({}, 'Something went wrong')).toBe('Something went wrong')
    expect(extractErrorMessage(undefined, 'Something went wrong')).toBe('Something went wrong')
  })

  it('ignores an empty message string and uses the fallback', () => {
    expect(extractErrorMessage({ message: '' }, 'fallback')).toBe('fallback')
  })
})
