<template>
  <div class="min-h-screen bg-gray-100">
    <header class="bg-white shadow">
      <nav
        class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8"
        aria-label="Main navigation"
      >
        <div class="flex h-16 items-center justify-between">
          <!-- Brand + desktop links -->
          <div class="flex items-center gap-6">
            <NuxtLink
              to="/"
              class="text-gray-900 font-semibold text-lg focus:outline-none focus:ring-2 focus:ring-black rounded"
              aria-label="Invoice Tracker home"
            >
              Invoice Tracker
            </NuxtLink>

            <ul class="hidden sm:flex gap-1 list-none m-0 p-0" role="list">
              <li>
                <NuxtLink
                  to="/"
                  class="text-sm text-gray-600 hover:text-gray-900 px-3 py-2 rounded focus:outline-none focus:ring-2 focus:ring-black"
                  active-class="!text-gray-900 font-semibold underline underline-offset-4"
                  exact-active-class="!text-gray-900 font-semibold underline underline-offset-4"
                  data-testid="nav-dashboard"
                >Dashboard</NuxtLink>
              </li>
              <li>
                <NuxtLink
                  to="/invoices"
                  class="text-sm text-gray-600 hover:text-gray-900 px-3 py-2 rounded focus:outline-none focus:ring-2 focus:ring-black"
                  active-class="!text-gray-900 font-semibold underline underline-offset-4"
                  data-testid="nav-invoices"
                >Invoices</NuxtLink>
              </li>
              <li>
                <NuxtLink
                  to="/clients"
                  class="text-sm text-gray-600 hover:text-gray-900 px-3 py-2 rounded focus:outline-none focus:ring-2 focus:ring-black"
                  active-class="!text-gray-900 font-semibold underline underline-offset-4"
                  data-testid="nav-clients"
                >Clients</NuxtLink>
              </li>
            </ul>
          </div>

          <!-- Desktop sign-out -->
          <button
            class="hidden sm:block text-sm text-gray-600 hover:text-gray-900 focus:outline-none focus:ring-2 focus:ring-black rounded px-2 py-1"
            data-testid="logout-button"
            @click="logout"
          >
            Sign out
          </button>

          <!-- Mobile hamburger -->
          <button
            class="sm:hidden p-2 rounded focus:outline-none focus:ring-2 focus:ring-black"
            :aria-expanded="mobileOpen"
            aria-controls="mobile-menu"
            aria-label="Toggle navigation menu"
            data-testid="nav-hamburger"
            @click="mobileOpen = !mobileOpen"
          >
            <svg class="h-5 w-5 text-gray-700" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
              <path
                v-if="mobileOpen"
                fill-rule="evenodd"
                clip-rule="evenodd"
                d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
              />
              <path
                v-else
                fill-rule="evenodd"
                clip-rule="evenodd"
                d="M3 5a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM3 10a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM3 15a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z"
              />
            </svg>
          </button>
        </div>

        <!-- Mobile menu panel -->
        <div
          v-if="mobileOpen"
          id="mobile-menu"
          class="sm:hidden border-t pb-4 pt-2"
          data-testid="nav-mobile-menu"
        >
          <ul class="flex flex-col gap-1 list-none m-0 p-0" role="list">
            <li>
              <NuxtLink
                to="/"
                class="block text-sm text-gray-700 hover:bg-gray-50 px-3 py-2 rounded focus:outline-none focus:ring-2 focus:ring-black"
                active-class="font-semibold bg-gray-100"
                exact-active-class="font-semibold bg-gray-100"
                @click="mobileOpen = false"
              >Dashboard</NuxtLink>
            </li>
            <li>
              <NuxtLink
                to="/invoices"
                class="block text-sm text-gray-700 hover:bg-gray-50 px-3 py-2 rounded focus:outline-none focus:ring-2 focus:ring-black"
                active-class="font-semibold bg-gray-100"
                @click="mobileOpen = false"
              >Invoices</NuxtLink>
            </li>
            <li>
              <NuxtLink
                to="/clients"
                class="block text-sm text-gray-700 hover:bg-gray-50 px-3 py-2 rounded focus:outline-none focus:ring-2 focus:ring-black"
                active-class="font-semibold bg-gray-100"
                @click="mobileOpen = false"
              >Clients</NuxtLink>
            </li>
          </ul>

          <div class="mt-3 border-t pt-3">
            <button
              class="text-sm text-gray-600 hover:text-gray-900 focus:outline-none focus:ring-2 focus:ring-black rounded px-3 py-2"
              data-testid="logout-button-mobile"
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
import { ref } from 'vue'
import { useAuth } from '~/composables/useAuth'

const { logout } = useAuth()
const mobileOpen = ref(false)
</script>