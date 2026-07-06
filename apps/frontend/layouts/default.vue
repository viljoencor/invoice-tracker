<template>
  <div class="min-h-screen bg-gray-100">
    <header class="bg-white shadow">
      <nav class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div class="flex h-16 justify-between items-center">
          <div class="flex">
            <NuxtLink to="/" class="text-gray-900 font-semibold">
              Invoice Tracker
            </NuxtLink>
          </div>
          <div class="flex items-center">
            <button
              class="text-sm text-gray-600 hover:text-gray-900"
              data-testid="logout-button"
              @click="logout"
            >
              Sign out
            </button>
          </div>
        </div>
      </nav>
    </header>

    <main class="py-10">
      <div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <AppErrorBoundary>
          <slot />
        </AppErrorBoundary>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { useAuth } from '~/composables/useAuth'
const { logout } = useAuth()
</script>
