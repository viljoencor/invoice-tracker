<script setup lang="ts">
import { computed, ref } from 'vue'

type Row = { month: string; total_cents: number; count?: number }

const props = withDefaults(defineProps<{
  data: Row[]
  height?: number         // total card height
  maxBars?: number
  currency?: string
}>(), {
  height: 220,
  maxBars: 12,
  currency: 'ZAR',
})

/* ----- data prep ----- */
const rows = computed<Row[]>(() => {
  const sorted = [...(props.data ?? [])].sort((a, b) => a.month.localeCompare(b.month))
  return sorted.slice(-props.maxBars)
})

const values = computed(() => rows.value.map(r => Number(r.total_cents || 0)))
const maxVal = computed(() => {
  const m = Math.max(1, ...values.value)
  // nice-ish ceiling
  const pow = 10 ** Math.floor(Math.log10(m))
  const step = [1, 2, 5, 10].find(s => m <= s * pow) ?? 10
  return step * pow
})
const avgVal = computed(() => (values.value.length ? values.value.reduce((a, b) => a + b, 0) / values.value.length : 0))

/* ----- sizing ----- */
const P = { t: 22, r: 12, b: 32, l: 32 } // inner padding
const W = 560, H = computed(() => props.height - 12) // base size; we’ll scale to width via CSS
const innerW = W - P.l - P.r
const innerH = computed(() => H.value - P.t - P.b)

const xStep = computed(() => (rows.value.length ? innerW / rows.value.length : innerW))
const barW = computed(() => Math.max(8, Math.min(18, xStep.value * 0.45)))

/* ----- scales ----- */
const y = (v: number) => {
  const h = innerH.value
  return P.t + (1 - v / maxVal.value) * h
}
const x = (i: number) => P.l + i * xStep.value + xStep.value / 2

/* ----- trend path (smoothed) ----- */
const trendD = computed(() => {
  const pts = rows.value.map((r, i) => [x(i), y(Number(r.total_cents || 0))])
  if (pts.length < 2) return ''
  const d: string[] = [`M ${pts[0][0]} ${pts[0][1]}`]
  for (let i = 1; i < pts.length; i++) {
    const [x0, y0] = pts[i - 1]
    const [x1, y1] = pts[i]
    const cx = (x0 + x1) / 2
    d.push(`C ${cx} ${y0}, ${cx} ${y1}, ${x1} ${y1}`)
  }
  return d.join(' ')
})

/* ----- active bar tooltip ----- */
const active = ref<number | null>(null)
const fmtMoney = (cents: number) =>
  new Intl.NumberFormat('en-ZA', { style: 'currency', currency: props.currency }).format(cents / 100)
const shortYM = (ym: string) => ym.slice(2) // "25-11"
</script>

<template>
  <div class="w-full bg-white rounded-2xl shadow p-4">
    <div class="flex items-center justify-between mb-2">
      <h2 class="text-lg font-semibold">Revenue</h2>
      <!-- MoM chip (computed inside parent; we’ll accept slot for flexibility later) -->
      <slot name="chip" />
    </div>

    <div class="relative">
      <svg
        :viewBox="`0 0 ${W} ${H}`"
        class="w-full"
        :style="{ height: `${height}px` }"
      >
        <!-- defs -->
        <defs>
          <linearGradient id="barGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="#3B82F6" stop-opacity="0.95"/>
            <stop offset="100%" stop-color="#60A5FA" stop-opacity="0.6"/>
          </linearGradient>
          <filter id="glow" height="200%" width="200%" x="-50%" y="-50%">
            <feGaussianBlur stdDeviation="4" result="coloredBlur"/>
            <feMerge>
              <feMergeNode in="coloredBlur"/>
              <feMergeNode in="SourceGraphic"/>
            </feMerge>
          </filter>
        </defs>

        <!-- grid: baseline + avg line -->
        <line
          :x1="P.l" :x2="W - P.r"
          :y1="P.t + innerH" :y2="P.t + innerH"
          stroke="#E5E7EB" stroke-width="1"
        />
        <line
          v-if="avgVal > 0"
          :x1="P.l" :x2="W - P.r"
          :y1="y(avgVal)" :y2="y(avgVal)"
          stroke="#94A3B8" stroke-dasharray="3 3" stroke-width="1"
        />
        <text v-if="avgVal > 0"
          :x="P.l" :y="y(avgVal) - 6"
          fill="#94A3B8" font-size="10">Avg {{ fmtMoney(avgVal) }}</text>

        <!-- bars -->
        <g>
          <template v-for="(r, i) in rows" :key="r.month">
            <rect
              :x="x(i) - barW/2" :y="y(Number(r.total_cents || 0))"
              :width="barW" :height="(P.t + innerH) - y(Number(r.total_cents || 0))"
              rx="4" ry="4"
              :fill="'url(#barGrad)'"
              class="transition-all duration-300"
              :filter="i === rows.length - 1 ? 'url(#glow)' : undefined"
              @mouseenter="active = i" @mouseleave="active = null"
            />
            <!-- hover dot on trend -->
            <circle
              :cx="x(i)" :cy="y(Number(r.total_cents || 0))"
              r="3"
              :fill="i === active ? '#1D4ED8' : '#60A5FA'"
              class="transition-colors duration-200"
            />
          </template>
        </g>

        <!-- smooth trend -->
        <path
          :d="trendD"
          fill="none"
          stroke="#2563EB"
          stroke-width="2"
          stroke-linecap="round"
          class="opacity-80"
        />

        <!-- x labels (first & last only) -->
        <text
          v-if="rows.length"
          :x="x(0)" :y="H - 8" text-anchor="middle"
          fill="#6B7280" font-size="10">{{ shortYM(rows[0].month) }}</text>
        <text
          v-if="rows.length > 1"
          :x="x(rows.length - 1)" :y="H - 8" text-anchor="middle"
          fill="#6B7280" font-size="10">{{ shortYM(rows[rows.length - 1].month) }}</text>
      </svg>

      <!-- tooltip -->
      <transition name="fade">
        <div
          v-if="active !== null"
          class="absolute -translate-x-1/2 -translate-y-full bg-white border border-gray-200 shadow-sm rounded px-2 py-1 text-[11px] text-gray-800"
          :style="{
            left: `calc(${(x(active) / W) * 100}% )`,
            top: `calc(${(y(Number(rows[active!].total_cents || 0)) / H) * 100}% )`
          }"
        >
          <div class="font-medium">{{ shortYM(rows[active!].month) }}</div>
          <div>{{ fmtMoney(Number(rows[active!].total_cents || 0)) }}</div>
          <div v-if="rows[active!].count" class="text-gray-500">
            {{ rows[active!].count }} invoice{{ rows[active!].count === 1 ? '' : 's' }}
          </div>
        </div>
      </transition>
    </div>
  </div>
</template>

<style scoped>
.fade-enter-active, .fade-leave-active { transition: opacity .15s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
