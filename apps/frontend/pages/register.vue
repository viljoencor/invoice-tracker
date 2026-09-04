<template>
  <div class="min-h-screen flex items-center justify-center p-6">
    <div class="w-full max-w-md space-y-6">
      <h1 class="text-2xl font-semibold text-center">Create your account</h1>

      <form class="space-y-4" @submit.prevent="onSubmit">
        <div>
          <label class="block text-sm mb-1">Name</label>
          <input
            v-model="name"
            type="text"
            required
            data-testid="register-name"
            class="w-full border rounded px-3 py-2"
            placeholder="Jane Doe"
          />
        </div>
        <div>
          <label class="block text-sm mb-1">Email</label>
          <input
            v-model="email"
            type="email"
            required
            data-testid="register-email"
            class="w-full border rounded px-3 py-2"
            placeholder="jane@example.com"
          />
        </div>
        <div>
          <label class="block text-sm mb-1">Password</label>
          <input
            v-model="password"
            :type="show ? 'text' : 'password'"
            required
            minlength="8"
            data-testid="register-password"
            class="w-full border rounded px-3 py-2"
            placeholder="••••••••"
          />
          <label class="inline-flex items-center gap-2 mt-2 text-sm">
            <input type="checkbox" v-model="show" />
            Show password
          </label>
        </div>

        <button
          type="submit"
          :disabled="loading"
          data-testid="register-submit"
          class="w-full bg-black text-white rounded px-4 py-2 disabled:opacity-50"
        >
          {{ loading ? 'Creating account…' : 'Create account' }}
        </button>

        <p v-if="error" data-testid="register-error" class="text-red-600 text-sm">{{ error }}</p>
      </form>

      <p class="text-sm text-center text-gray-600">
        Already have an account?
        <NuxtLink to="/login" data-testid="register-login-link" class="font-medium text-black underline">
          Sign in
        </NuxtLink>
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

definePageMeta({ layout: 'auth', middleware: 'auth' })

const name = ref('')
const email = ref('')
const password = ref('')
const show = ref(false)
const loading = ref(false)
const error = ref<string | null>(null)

async function onSubmit() {
  loading.value = true
  error.value = null
  try {
    // BFF sets httpOnly cookies and signs the new account in immediately — no
    // token handling in client code, mirroring the login flow.
    await $fetch('/api/auth/register', {
      method: 'POST',
      body: { name: name.value, email: email.value, password: password.value },
      credentials: 'include',
    })
    // Hard navigation so the browser sends the new session cookie in the SSR request,
    // bypassing stale useCookie state that persists from the server-rendered page.
    window.location.href = '/'
  } catch (e: any) {
    error.value =
      e?.data?.message ||
      e?.data?.detail?.message ||
      e?.data?.detail ||
      e?.message ||
      'Registration failed'
  } finally {
    loading.value = false
  }
}
</script>
