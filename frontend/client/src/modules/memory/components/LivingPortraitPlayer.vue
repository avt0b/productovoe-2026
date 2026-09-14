<script setup lang="ts">
import { onBeforeUnmount, ref } from 'vue'

import MsIcon from '@/ui/MsIcon.vue'

defineProps<{
  image: string
  line: string
}>()

/** Сколько длится вспышка «перезапуска» портрета. */
const REPLAY_FLASH_MS = 600

const muted = ref(false)
const slow = ref(false)
const replaying = ref(false)
let replayTimer: ReturnType<typeof setTimeout> | undefined

/**
 * Видео живого портрета ещё нет — движение изображается «дыханием» кадра.
 * Когда появится ролик из `media_service`, заменится содержимое окна просмотра,
 * а кнопки останутся.
 */
function replay(): void {
  replaying.value = false
  // Сброс на следующем кадре, чтобы анимация повторилась при быстром двойном нажатии.
  requestAnimationFrame(() => {
    replaying.value = true
    clearTimeout(replayTimer)
    replayTimer = setTimeout(() => (replaying.value = false), REPLAY_FLASH_MS)
  })
}

onBeforeUnmount(() => clearTimeout(replayTimer))
</script>

<template>
  <div class="relative flex flex-col space-y-3 overflow-hidden rounded-sheet bg-inverse-surface p-3 text-inverse-on-surface shadow-xl">
    <div class="relative flex aspect-[4/5] w-full items-end overflow-hidden rounded-[22px] bg-surface-dim">
      <img
        :src="image"
        alt="Реконструированный портрет героя"
        class="portrait absolute inset-0 h-full w-full object-cover object-top"
        :class="{ 'portrait--slow': slow, 'portrait--flash': replaying }"
      />
      <div class="pointer-events-none absolute inset-0 bg-gradient-to-t from-black/90 via-black/25 to-black/40" />

      <div class="pointer-events-none absolute inset-x-3 top-3 flex items-center justify-between">
        <div class="flex items-center gap-1.5 rounded-full bg-black/50 px-3 py-1.5 text-white shadow-sm backdrop-blur-md">
          <span class="h-2 w-2 animate-pulse rounded-full bg-secondary-fixed-dim" />
          <span class="font-label-sm text-label-sm">Нейрореставрация</span>
        </div>
        <!-- В макете было «Аутентичный голос». Голос синтезирован — выдавать его за подлинный нельзя. -->
        <div class="flex items-center gap-1.5 rounded-full bg-black/50 px-3 py-1.5 text-white shadow-sm backdrop-blur-md">
          <MsIcon name="graphic_eq" :size="14" class="text-tertiary-fixed" />
          <span class="font-label-sm text-label-sm">Реконструкция голоса</span>
        </div>
      </div>

      <div class="relative z-10 w-full p-2.5">
        <div class="flex items-center gap-2.5 rounded-xl bg-black/65 p-3 shadow-lg backdrop-blur-md">
          <MsIcon name="format_quote" :size="20" filled class="shrink-0 text-tertiary-fixed" />
          <p class="font-body-sm text-body-sm italic leading-snug text-white">{{ line }}</p>
        </div>
      </div>
    </div>

    <div class="flex items-center justify-between px-2 pb-2 pt-1">
      <button
        type="button"
        class="flex h-11 items-center gap-2 rounded-full bg-surface-container/20 px-4 text-inverse-on-surface transition-all hover:bg-surface-container/30 active:scale-95"
        :class="{ 'opacity-60': muted }"
        :aria-pressed="muted"
        @click="muted = !muted"
      >
        <MsIcon :name="muted ? 'volume_off' : 'volume_up'" :size="20" />
        <span class="font-label-md text-label-md">{{ muted ? 'Без звука' : 'Звук вкл' }}</span>
      </button>

      <button
        type="button"
        aria-label="Перезапустить видеопортрет"
        class="flex h-12 w-12 items-center justify-center rounded-full bg-primary text-on-primary shadow-lg shadow-primary/40 transition-transform duration-300 active:scale-90"
        :class="{ 'rotate-[360deg]': replaying }"
        @click="replay"
      >
        <MsIcon name="replay" filled />
      </button>

      <button
        type="button"
        class="flex h-11 items-center gap-1.5 rounded-full bg-surface-container/20 px-4 transition-all hover:bg-surface-container/30 active:scale-95"
        :class="slow ? 'text-tertiary-fixed' : 'text-inverse-on-surface'"
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
