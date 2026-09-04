<template>
  <div class="min-h-screen bg-gray-100">
    <header class="bg-white shadow">
      <nav
        class="w-full px-4 sm:px-6 lg:px-8"
        aria-label="Main navigation"
      >
        <div
          class="h-16"
          style="display: flex; align-items: center; width: 100%;"
        >
          <!-- Brand -->
          <NuxtLink
            to="/"
            class="text-lg font-semibold text-gray-900 rounded focus:outline-none focus:ring-2 focus:ring-black"
            aria-label="Invoice Tracker home"
          >
            Invoice Tracker
          </NuxtLink>

          <!-- Desktop navigation -->
          <ul
            class="hidden sm:flex items-center gap-1 list-none p-0"
            style="margin: 0 0 0 1rem;"
            role="list"
          >
            <li>
              <NuxtLink
                to="/"
                class="text-sm text-gray-600 hover:text-gray-900 px-3 py-2 rounded focus:outline-none focus:ring-2 focus:ring-black"
                active-class="!text-gray-900 font-semibold underline underline-offset-4"
                exact-active-class="!text-gray-900 font-semibold underline underline-offset-4"
                data-testid="nav-dashboard"
              >
                Dashboard
              </NuxtLink>
            </li>

            <li>
              <NuxtLink
                to="/invoices"
                class="text-sm text-gray-600 hover:text-gray-900 px-3 py-2 rounded focus:outline-none focus:ring-2 focus:ring-black"
                active-class="!text-gray-900 font-semibold underline underline-offset-4"
                data-testid="nav-invoices"
              >
                Invoices
              </NuxtLink>
            </li>

            <li>
              <NuxtLink
                to="/clients"
                class="text-sm text-gray-600 hover:text-gray-900 px-3 py-2 rounded focus:outline-none focus:ring-2 focus:ring-black"
                active-class="!text-gray-900 font-semibold underline underline-offset-4"
                data-testid="nav-clients"
              >
                Clients
              </NuxtLink>
            </li>
          </ul>

          <!--
            RIGHT CONTROLS

            margin-left: auto is what physically pushes
            this entire container to the far right.
          -->
          <div
            style="
              margin-left: auto;
              display: flex;
              align-items: center;
              gap: 0.75rem;
              flex-shrink: 0;
            "
          >
            <!-- Mobile hamburger -->
            <button
              class="sm:hidden p-2 rounded focus:outline-none focus:ring-2 focus:ring-black"
              :aria-expanded="mobileOpen"
              aria-controls="mobile-menu"
              aria-label="Toggle navigation menu"
              data-testid="nav-hamburger"
              @click="mobileOpen = !mobileOpen"
            >
              <svg
                class="h-5 w-5 text-gray-700"
                viewBox="0 0 20 20"
                fill="currentColor"
                aria-hidden="true"
              >
                <!-- Close -->
                <path
                  v-if="mobileOpen"
                  fill-rule="evenodd"
                  clip-rule="evenodd"
                  d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                />

                <!-- Hamburger -->
                <path
                  v-else
                  fill-rule="evenodd"
                  clip-rule="evenodd"
                  d="M3 5a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM3 10a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM3 15a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z"
                />
              </svg>
            </button>

            <!-- Sign out -->
            <button
              class="text-sm text-gray-600 hover:text-gray-900 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-black whitespace-nowrap"
              data-testid="logout-button"
              @click="logout"
            >
              Sign out
            </button>
          </div>
        </div>

        <!-- Mobile menu -->
        <div
          v-if="mobileOpen"
          id="mobile-menu"
          class="sm:hidden border-t pb-4 pt-2"
          data-testid="nav-mobile-menu"
        >
          <ul
            class="flex flex-col gap-1 list-none m-0 p-0"
            role="list"
          >
            <li>
              <NuxtLink
                to="/"
                class="block text-sm text-gray-700 hover:bg-gray-50 px-3 py-2 rounded focus:outline-none focus:ring-2 focus:ring-black"
                active-class="font-semibold bg-gray-100"
                exact-active-class="font-semibold bg-gray-100"
                @click="mobileOpen = false"
              >
                Dashboard
              </NuxtLink>
            </li>

            <li>
              <NuxtLink
                to="/invoices"
                class="block text-sm text-gray-700 hover:bg-gray-50 px-3 py-2 rounded focus:outline-none focus:ring-2 focus:ring-black"
                active-class="font-semibold bg-gray-100"
                @click="mobileOpen = false"
              >
                Invoices
              </NuxtLink>
            </li>

            <li>
              <NuxtLink
                to="/clients"
                class="block text-sm text-gray-700 hover:bg-gray-50 px-3 py-2 rounded focus:outline-none focus:ring-2 focus:ring-black"
                active-class="font-semibold bg-gray-100"
                @click="mobileOpen = false"
              >
                Clients
              </NuxtLink>
            </li>
          </ul>
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