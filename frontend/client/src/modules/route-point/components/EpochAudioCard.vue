<script setup lang="ts">
import { onBeforeUnmount, ref } from 'vue'

import MsIcon from '@/ui/MsIcon.vue'

/**
 * Голос эпохи: запись рассказа о точке из `route_service` (`audio_url`).
 *
 * Играет настоящий файл через `<audio>`: раньше карточка изображала плеер
 * таймером и случайными полосками, и человек слышал тишину, глядя на бегущую
 * дорожку. Нет записи у точки — карточки на экране нет вовсе.
 */
const props = defineProps<{
  src: string
  title: string
  /** Кто читает или откуда запись. Пусто — строку не показываем. */
  author?: string
}>()

const audio = ref<HTMLAudioElement | null>(null)
const playing = ref(false)
const position = ref(0)
const duration = ref(0)
const failed = ref(false)

/** Полоски дорожки: в покое неровные, при игре качаются — это отражение звука, а не его подделка. */
const RESTING_BARS = [8, 16, 24, 12, 20, 16, 24, 8, 20, 12, 16, 8]
const BAR_TICK_MS = 250
const bars = ref([...RESTING_BARS])
let barsTimer: ReturnType<typeof setInterval> | undefined

function startBars(): void {
  stopBars()
  barsTimer = setInterval(() => {
    bars.value = bars.value.map(() => 6 + Math.floor(Math.random() * 18))
  }, BAR_TICK_MS)
}

function stopBars(): void {
  clearInterval(barsTimer)
  barsTimer = undefined
  bars.value = [...RESTING_BARS]
}

async function toggle(): Promise<void> {
  const element = audio.value
  if (!element || failed.value) return
  if (playing.value) {
    element.pause()
    return
  }
  try {
    await element.play()
  } catch {
    // Браузер не дал играть (нет жеста, нет файла) — показываем это, а не делаем вид, что играет.
    failed.value = true
  }
}

function seek(event: Event): void {
  const element = audio.value
  if (!element) return
  element.currentTime = Number((event.target as HTMLInputElement).value)
}

function clock(seconds: number): string {
  const total = Math.max(0, Math.round(seconds))
  return `${Math.floor(total / 60)}:${String(total % 60).padStart(2, '0')}`
}

onBeforeUnmount(stopBars)
</script>

<template>
  <section class="flex flex-col gap-space-sm rounded-2xl bg-surface-container-lowest p-space-md shadow-document">
    <audio
      ref="audio"
      :src="props.src"
      preload="metadata"
      @loadedmetadata="duration = audio?.duration ?? 0"
      @timeupdate="position = audio?.currentTime ?? 0"
      @play="((playing = true), startBars())"
      @pause="((playing = false), stopBars())"
      @ended="((playing = false), (position = 0), stopBars())"
      @error="failed = true"
    />

    <div class="flex items-center gap-space-sm">
      <button
        type="button"
        class="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-primary-container text-white shadow-stamp transition-colors hover:bg-primary disabled:opacity-60"
        :aria-label="playing ? 'Пауза' : 'Слушать'"
        :disabled="failed"
        @click="toggle"
      >
        <MsIcon :name="playing ? 'pause' : 'play_arrow'" :size="24" filled />
      </button>

      <div class="min-w-0 flex-1">
        <p class="font-archival text-archival uppercase text-on-surface-variant">Голос эпохи</p>
        <p class="truncate font-label-lg text-label-lg text-on-surface">{{ title }}</p>
        <p v-if="author" class="truncate font-body-sm text-body-sm text-on-surface-variant">{{ author }}</p>
      </div>

      <!-- Дорожка: качается, только пока звук идёт -->
      <div class="flex h-8 shrink-0 items-end gap-0.5" aria-hidden="true">
        <span
          v-for="(height, index) in bars"
          :key="index"
          class="w-0.5 rounded-full bg-secondary transition-all duration-200"
          :style="{ height: `${height}px` }"
        />
      </div>
    </div>

    <p v-if="failed" class="font-body-sm text-body-sm text-error">Запись не открылась — попробуйте позже.</p>

    <div v-else class="flex items-center gap-space-sm">
      <span class="w-10 shrink-0 font-label-sm text-label-sm text-on-surface-variant">{{ clock(position) }}</span>
      <label class="relative flex min-w-0 flex-1 items-center">
        <span class="sr-only">Перемотка записи</span>
        <input
          type="range"
          min="0"
          :max="duration || 0"
          step="1"
          :value="position"
          class="h-1 w-full cursor-pointer appearance-none rounded-full bg-surface-container-high accent-primary"
          @input="seek"
        />
      </label>
      <span class="w-10 shrink-0 text-right font-label-sm text-label-sm text-on-surface-variant">{{ clock(duration) }}</span>
    </div>
  </section>
</template>
