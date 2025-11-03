<script setup lang="ts">
definePageMeta({ middleware: 'auth' })
await navigateTo('/') // our real dashboard lives at "/"
</script>

<template></template>