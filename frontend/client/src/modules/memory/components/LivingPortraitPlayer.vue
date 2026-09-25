<script setup lang="ts">
import { onBeforeUnmount, ref, watch } from 'vue'

import MsIcon from '@/ui/MsIcon.vue'

const props = defineProps<{
  /** Фото бойца. Пока видео нет — движение изображается «дыханием» кадра. */
  image: string
  /** Готовый ролик из `media_service`. */
  videoUrl?: string | null
  line: string
  /** Подпись в углу: имя бойца или «Пример оформления». */
  caption: string
}>()

/** Сколько длится вспышка «перезапуска» портрета. */
const REPLAY_FLASH_MS = 600

const muted = ref(true)
const slow = ref(false)
const replaying = ref(false)
const video = ref<HTMLVideoElement | null>(null)
let replayTimer: ReturnType<typeof setTimeout> | undefined

watch(slow, (value) => {
  if (video.value) video.value.playbackRate = value ? 0.5 : 1
})

function replay(): void {
  if (video.value) {
    video.value.currentTime = 0
    void video.value.play()
  }
  replaying.value = false
  // Сброс на следующем кадре, чтобы анимация повторилась при быстром двойном нажатии.
  requestAnimationFrame(() => {
    replaying.value = true
    clearTimeout(replayTimer)
    replayTimer = setTimeout(() => (replaying.value = false), REPLAY_FLASH_MS)
  })
}

onBeforeUnmount(() => clearTimeout(replayTimer))

// Новый клип — с начала и с тем же темпом.
watch(
  () => props.videoUrl,
  () => requestAnimationFrame(() => video.value && (video.value.playbackRate = slow.value ? 0.5 : 1)),
)
</script>

<template>
  <!-- Тёмная сцена — одно из мест, где DESIGN разрешает ночь: под ней фото и видео. -->
  <div class="relative flex flex-col gap-space-sm overflow-hidden rounded-sheet bg-night p-space-sm text-white shadow-sheet">
    <div class="relative flex aspect-[4/5] w-full items-end overflow-hidden rounded-2xl bg-night-soft short:aspect-square">
      <video
        v-if="videoUrl"
        ref="video"
        :src="videoUrl"
        :poster="image"
        :muted="muted"
        autoplay
        loop
        playsinline
        class="absolute inset-0 h-full w-full object-cover object-top"
      />
      <img
        v-else
        :src="image"
        alt="Фото героя"
        class="portrait absolute inset-0 h-full w-full object-cover object-top"
        :class="{ 'portrait--slow': slow, 'portrait--flash': replaying }"
      />
      <div class="pointer-events-none absolute inset-0 bg-gradient-to-b from-night/20 via-transparent to-night/70" />

      <div class="pointer-events-none absolute inset-x-3 top-3 flex items-center justify-between gap-2">
        <div class="flex min-w-0 items-center gap-1.5 rounded-full border border-white/15 bg-night/45 px-space-sm py-1 text-white backdrop-blur-md">
          <span class="h-2 w-2 shrink-0 rounded-full bg-secondary-fixed-dim motion-safe:animate-pulse" />
          <span class="truncate font-label-sm text-label-sm">{{ caption }}</span>
        </div>
        <!-- Голос синтезирован — выдавать его за подлинный нельзя. -->
        <div class="flex shrink-0 items-center gap-1.5 rounded-full border border-white/15 bg-night/45 px-space-sm py-1 text-white backdrop-blur-md">
          <MsIcon name="graphic_eq" :size="15" class="text-tertiary-fixed" />
          <span class="font-label-sm text-label-sm">Реконструкция</span>
        </div>
      </div>

      <div class="relative z-10 w-full p-space-sm">
        <div class="flex items-center gap-space-sm rounded-2xl border border-white/15 bg-night/45 p-space-sm shadow-sheet backdrop-blur-md">
          <MsIcon name="format_quote" :size="20" filled class="shrink-0 text-tertiary-fixed" />
          <p class="font-body-sm text-body-sm italic leading-snug text-white">«{{ line }}»</p>
        </div>
      </div>
    </div>

    <div class="flex items-center justify-between px-space-xs pb-space-xs">
      <!-- Звук есть только у готового видео; у фото-примера кнопки нет, а не выключенная пустышка. -->
      <button
        v-if="videoUrl"
        type="button"
        class="flex h-11 items-center gap-2 rounded-full bg-white/10 px-space-md text-white transition-colors duration-200 hover:bg-white/15 active:scale-95"
        :class="{ 'text-white/70': muted }"
        :aria-pressed="!muted"
        @click="muted = !muted"
      >
        <MsIcon :name="muted ? 'volume_off' : 'volume_up'" :size="20" />
        <span class="font-label-md text-label-md">{{ muted ? 'Без звука' : 'Звук вкл' }}</span>
      </button>
      <span v-else class="font-label-sm text-label-sm text-white/70">Фото «дышит» — видео ещё нет</span>

      <button
        type="button"
        aria-label="Перезапустить видеопортрет"
        class="flex h-12 w-12 items-center justify-center rounded-full border border-white/15 bg-white/15 text-white backdrop-blur-md transition-transform duration-300 active:scale-90"
        :class="{ 'rotate-[360deg]': replaying }"
        @click="replay"
      >
        <MsIcon name="replay" filled />
      </button>

      <button
        type="button"
        class="flex h-11 items-center gap-1.5 rounded-full bg-white/10 px-space-md transition-colors duration-200 hover:bg-white/15 active:scale-95"
        :class="slow ? 'text-tertiary-fixed' : 'text-white'"
        :aria-pressed="slow"
        aria-label="Замедленное воспроизведение"
        @click="slow = !slow"
      >
        <MsIcon name="slow_motion_video" :size="18" />
        <span class="font-label-md text-label-md">{{ slow ? '0.5x' : '1.0x' }}</span>
      </button>
    </div>
  </div>
</template>

<style scoped>
/* «Дыхание» портрета: едва заметный вдох раз в пять секунд. */
.portrait {
  animation: breathe 4.8s ease-in-out infinite;
  transition: filter 0.6s ease-out;
}
.portrait--slow {
  animation-duration: 9.6s;
}
.portrait--flash {
  filter: brightness(1.15) contrast(1.05);
}

@keyframes breathe {
  0%,
  100% {
    transform: scale(1) translateY(0);
  }
  50% {
    transform: scale(1.03) translateY(-4px);
  }
}

/* Кто попросил систему не двигать интерфейс — портрет стоит неподвижно. */
@media (prefers-reduced-motion: reduce) {
  .portrait {
    animation: none;
  }
}
</style>
