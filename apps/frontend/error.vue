<script setup lang="ts">
import type { NuxtError } from '#app'

const props = defineProps<{ error: NuxtError }>()
const isDev = import.meta.env.DEV

function handleReload() {
  clearError({ redirect: '/' })
}
</script>

<template>
  <div
    data-testid="app-error-page"
    class="min-h-screen flex flex-col items-center justify-center p-8 bg-gray-50"
  >
    <div class="max-w-md w-full text-center space-y-4">
      <h1 class="text-2xl font-semibold text-gray-900">Application Error</h1>
      <p
        v-if="isDev"
        data-testid="error-message"
        class="text-gray-600 font-mono text-sm break-all"
      >
        {{ error.message }}
      </p>
      <p v-else class="text-gray-600">
        An unexpected error occurred. Please try again.
      </p>
      <button
        data-testid="app-error-reload"
        class="bg-black text-white rounded px-6 py-2"
        @click="handleReload"
      >
        Return to App
      </button>
    </div>
  </div>
</template>
