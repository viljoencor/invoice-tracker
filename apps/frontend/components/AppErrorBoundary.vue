<script setup lang="ts">
import { ref, computed, onErrorCaptured } from 'vue'

const error = ref<Error | null>(null)
const hasError = computed(() => error.value !== null)
const isDev = import.meta.env.DEV

const emit = defineEmits<{ (e: 'error', err: Error): void }>()

onErrorCaptured((err: Error) => {
  error.value = err
  emit('error', err)
  if (isDev) {
    // eslint-disable-next-line no-console
    console.error('[AppErrorBoundary] caught:', err)
  }
  return false
})

function recover() {
  error.value = null
}
</script>

<template>
  <div
    v-if="hasError"
    data-testid="error-boundary-fallback"
    class="rounded-lg border border-red-200 bg-red-50 p-6 text-center"
  >
    <h2 class="text-lg font-semibold text-red-800 mb-2">Something went wrong</h2>
    <p
      v-if="isDev"
      data-testid="error-boundary-message"
      class="text-sm text-red-600 font-mono mb-4"
    >
      {{ error?.message }}
    </p>
    <p v-else class="text-sm text-gray-600 mb-4">An unexpected error occurred.</p>
    <div class="flex gap-2 justify-center">
      <button
        data-testid="error-boundary-retry"
        class="px-4 py-2 rounded bg-black text-white text-sm"
        @click="recover"
      >
        Try again
      </button>
      <NuxtLink
        to="/dashboard"
        data-testid="error-boundary-home"
        class="px-4 py-2 rounded border border-gray-300 text-sm"
      >
        Back to Dashboard
      </NuxtLink>
    </div>
  </div>
  <slot v-else />
</template>
