<template>
  <div class="p-4 rounded-2xl shadow bg-white">
    <div class="text-sm text-gray-500">{{ label }}</div>
    <div class="flex items-baseline gap-1">
      <div class="text-2xl font-semibold">{{ value }}</div>
      <div v-if="unit" class="text-sm text-gray-500">{{ unit }}</div>
    </div>
    <div v-if="trend" :class="[
      'text-sm mt-1',
      trendColor === 'green' ? 'text-green-600' :
      trendColor === 'red' ? 'text-red-600' :
      trendColor === 'yellow' ? 'text-yellow-600' :
      'text-gray-600'
    ]">
      {{ trend }}
    </div>
  </div>
</template>

<script setup lang="ts">
interface Props {
  label: string
  value: string | number
  unit?: string
  trend?: string
  trendColor?: 'red' | 'green' | 'yellow' | 'gray'
}

defineProps<Props>()
</script>