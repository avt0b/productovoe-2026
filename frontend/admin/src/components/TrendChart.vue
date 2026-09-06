<script setup lang="ts">
import { computed } from 'vue'

import type { Series } from '@/api/types'

const props = defineProps<{ series: Series[] }>()

const COLORS = ['#324523', '#51643a', '#b86b14']

const W = 720
const H = 260
const PAD = { top: 16, right: 16, bottom: 28, left: 48 }
const innerW = W - PAD.left - PAD.right
const innerH = H - PAD.top - PAD.bottom

/** Ряды приходят с разными наборами дат — сводим к общей оси. */
const axis = computed(() => {
  const dates = new Set<string>()
  for (const s of props.series) for (const p of s.points) dates.add(p.date)
  return [...dates].sort()
})

const maxValue = computed(() => {
  let max = 0
  for (const s of props.series) for (const p of s.points) max = Math.max(max, p.value)
  return Math.max(max, 1)
})

const isEmpty = computed(() => axis.value.length === 0)

function x(index: number): number {
  if (axis.value.length <= 1) return PAD.left + innerW / 2
  return PAD.left + (index * innerW) / (axis.value.length - 1)
}

function y(value: number): number {
  return PAD.top + innerH - (value / maxValue.value) * innerH
}

interface Line {
  key: string
  label: string
  color: string
  points: string
  dots: Array<{ cx: number; cy: number }>
  total: number
}

const lines = computed<Line[]>(() =>
  props.series.map((s, i) => {
    const byDate = new Map(s.points.map((p) => [p.date, p.value]))
    const coords = axis.value.map((date, index) => ({
      cx: x(index),
      cy: y(byDate.get(date) ?? 0),
    }))
    return {
      key: s.key,
      label: s.label,
      color: COLORS[i % COLORS.length]!,
      points: coords.map((c) => `${c.cx.toFixed(1)},${c.cy.toFixed(1)}`).join(' '),
      // Точки рисуем только когда их немного, иначе линия превращается в кашу.
      dots: coords.length <= 14 ? coords : [],
      total: s.points.reduce((sum, p) => sum + p.value, 0),
    }
  }),
)

const gridLines = computed(() =>
  [0, 0.25, 0.5, 0.75, 1].map((ratio) => ({
    y: PAD.top + innerH - ratio * innerH,
    label: Math.round(maxValue.value * ratio).toString(),
  })),
)

/** Не больше шести подписей на оси X, иначе они наезжают друг на друга. */
const xLabels = computed(() => {
  const dates = axis.value
  if (dates.length === 0) return []
  const step = Math.max(1, Math.ceil(dates.length / 6))
  const out: Array<{ x: number; label: string }> = []
  for (let i = 0; i < dates.length; i += step) {
    const parts = dates[i]!.split('-')
    out.push({ x: x(i), label: `${parts[2]}.${parts[1]}` })
  }
  return out
})
</script>

<template>
  <div class="flex flex-col gap-space-3">
    <div class="flex flex-wrap items-center gap-space-4">
      <div v-for="line in lines" :key="line.key" class="flex items-center gap-space-2">
        <span class="h-1 w-3 rounded-full" :style="{ backgroundColor: line.color }" />
        <span class="font-label-archive-code text-label-archive-code text-on-surface-variant">
          {{ line.label }}
          <span class="text-on-surface">· {{ line.total }}</span>
        </span>
      </div>
    </div>

    <div
      v-if="isEmpty"
      class="flex h-52 items-center justify-center rounded-lg bg-surface-container/50 text-on-surface-variant"
    >
      <span class="font-body-sm text-body-sm">За выбранный период данных нет</span>
    </div>

    <svg
      v-else
      class="w-full"
      :viewBox="`0 0 ${W} ${H}`"
      preserveAspectRatio="none"
      role="img"
      aria-label="Динамика по дням"
    >
      <line
        v-for="grid in gridLines"
        :key="`g-${grid.y}`"
        :x1="PAD.left"
        :x2="W - PAD.right"
        :y1="grid.y"
        :y2="grid.y"
        stroke="#e5e2da"
        stroke-dasharray="3,3"
        stroke-width="1"
      />
      <text
        v-for="grid in gridLines"
        :key="`t-${grid.y}`"
        :x="PAD.left - 8"
        :y="grid.y + 4"
        text-anchor="end"
        fill="#75786e"
        font-family="Space Mono"
        font-size="10"
      >
        {{ grid.label }}
      </text>

      <g v-for="line in lines" :key="line.key">
        <polyline
          :points="line.points"
          fill="none"
          :stroke="line.color"
          stroke-width="2.5"
          stroke-linecap="round"
          stroke-linejoin="round"
        />
        <circle
          v-for="(dot, i) in line.dots"
          :key="`${line.key}-${i}`"
          :cx="dot.cx"
          :cy="dot.cy"
          r="3.5"
          :fill="line.color"
          stroke="#fcf9f1"
          stroke-width="1.5"
        />
      </g>

      <text
        v-for="label in xLabels"
        :key="`x-${label.x}`"
        :x="label.x"
        :y="H - 8"
        text-anchor="middle"
        fill="#75786e"
        font-family="Space Mono"
        font-size="10"
      >
        {{ label.label }}
      </text>
    </svg>
  </div>
</template>
