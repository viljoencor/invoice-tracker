<template>
  <div class="min-h-screen bg-gray-100">
    <main class="py-10">
      <AppErrorBoundary>
        <slot />
      </AppErrorBoundary>
    </main>
  </div>
</template>

<script setup lang="ts">
// Minimal layout for unauthenticated pages (login, register) — no nav/sign-out,
// since those only make sense once a session exists.
</script>
