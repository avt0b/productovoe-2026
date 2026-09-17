<script setup lang="ts">
import { computed, onBeforeUnmount, ref } from 'vue'

import MsIcon from '@/ui/MsIcon.vue'

const props = defineProps<{
  title: string
  author: string
  durationSeconds: number
  positionSeconds: number
}>()

/** Полоски в покое — неровные, как в макете, а не гребёнка одной высоты. */
const RESTING_BARS = [8, 16, 24, 12, 20, 16, 24, 8, 20, 12, 16, 8]
const BAR_TICK_MS = 250

const playing = ref(false)
const position = ref(props.positionSeconds)
const bars = ref([...RESTING_BARS])

let clockTimer: ReturnType<typeof setInterval> | undefined
let barsTimer: ReturnType<typeof setInterval> | undefined

/**
 * Воспроизведение пока изображается: настоящего аудиофайла у точки ещё нет.
 * Таймер и полоски ведут себя как у плеера, чтобы экран можно было показать.
 */
function play(): void {
  if (position.value >= props.durationSeconds) position.value = 0
  playing.value = true
  clockTimer = setInterval(() => {
    position.value += 1
    if (position.value >= props.durationSeconds) pause()
  }, 1000)
  barsTimer = setInterval(() => {
    bars.value = bars.value.map(() => 6 + Math.floor(Math.random() * 18))
  }, BAR_TICK_MS)
}

function pause(): void {
  playing.value = false
  clearInterval(clockTimer)
  clearInterval(barsTimer)
  bars.value = [...RESTING_BARS]
}

function toggle(): void {
  if (playing.value) pause()
  else play()
}

// Ушли с экрана — таймеры не должны тикать в пустоту.
onBeforeUnmount(pause)

function clock(seconds: number): string {
  const safe = Math.max(0, Math.floor(seconds))
  return `${String(Math.floor(safe / 60)).padStart(2, '0')}:${String(safe % 60).padStart(2, '0')}`
}

const timeLabel = computed(() => `${clock(position.value)} / ${clock(props.durationSeconds)}`)
</script>

<template>
  <div class="flex flex-col gap-space-sm rounded-DEFAULT bg-secondary-container/30 p-space-md shadow-sm">
    <div class="flex items-start justify-between gap-space-sm">
      <div class="flex items-center gap-space-xs">
        <div class="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-secondary-container text-on-secondary-container">
          <MsIcon name="radio" :size="18" />
        </div>
        <div class="flex flex-col">
          <span class="font-label-lg text-label-lg leading-tight text-on-surface">{{ title }}</span>
          <span class="font-body-sm text-body-sm text-on-surface-variant">{{ author }}</span>
        </div>
      </div>
      <button
        type="button"
        class="flex shrink-0 items-center gap-1.5 rounded-full bg-secondary px-3 py-1.5 font-label-md text-label-md text-on-secondary shadow-sm transition-transform active:scale-95"
        :aria-label="playing ? 'Пауза' : 'Воспроизвести аудио'"
        @click="toggle"
      >
        <MsIcon :name="playing ? 'pause' : 'play_arrow'" :size="18" />
        <span>{{ playing ? 'Пауза' : 'Слушать' }}</span>
      </button>
    </div>

    <div class="flex items-center gap-space-sm pt-space-xs">
      <div class="flex h-6 flex-1 items-end gap-[3px] px-1" aria-hidden="true">
        <span
          v-for="(height, index) in bars"
          :key="index"
          class="w-1 rounded-full bg-secondary transition-all duration-300"
          :class="{ 'opacity-50': index % 3 === 0 }"
          :style="{ height: `${height}px` }"
        />
      </div>
      <span class="shrink-0 font-label-md text-label-md tabular-nums text-on-surface-variant">{{ timeLabel }}</span>
    </div>
  </div>
</template>
