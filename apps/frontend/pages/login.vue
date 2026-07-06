<template>
  <div class="min-h-screen flex items-center justify-center p-6">
    <div class="w-full max-w-md space-y-6">
      <h1 class="text-2xl font-semibold text-center">Sign in</h1>

      <form class="space-y-4" @submit.prevent="onSubmit">
        <div>
          <label class="block text-sm mb-1">Email</label>
          <input
            v-model="email"
            type="email"
            required
            data-testid="login-email"
            class="w-full border rounded px-3 py-2"
            placeholder="admin@example.com"
          />
        </div>
        <div>
          <label class="block text-sm mb-1">Password</label>
          <input
            v-model="password"
            :type="show ? 'text' : 'password'"
            required
            data-testid="login-password"
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
          data-testid="login-submit"
          class="w-full bg-black text-white rounded px-4 py-2 disabled:opacity-50"
        >
          {{ loading ? 'Signing in…' : 'Sign in' }}
        </button>

        <p v-if="error" data-testid="login-error" class="text-red-600 text-sm">{{ error }}</p>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
const email = ref('')
const password = ref('')
const show = ref(false)
const loading = ref(false)
const error = ref<string | null>(null)

const tokenCookie = useCookie<string | null>('token', { sameSite: 'lax' })
const api = useApi()

async function onSubmit() {
  loading.value = true
  error.value = null
  try {
    // Backend returns { access_token, token_type: "bearer" }
    const res = await api.post('/auth/login', { email: email.value, password: password.value })
    const { access_token } = res as any

    // Store ONLY the raw JWT; the composable adds "Bearer " properly
    tokenCookie.value = access_token

    await navigateTo('/') // dashboard lives at "/"
  } catch (e: any) {
    error.value =
      e?.data?.detail?.message ||
      e?.data?.detail ||
      e?.message ||
      'Login failed'
  } finally {
    loading.value = false
  }
}
</script>
