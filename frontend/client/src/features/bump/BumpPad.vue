<script setup lang="ts">
import type { UserPosition } from '@/core/geo'
import MsIcon from '@/ui/MsIcon.vue'

/**
 * Экран тряски: круг дышит в такт силе встряски, кнопка «Встряхнуть» — там,
 * где датчика нет (компьютер, запрещённый доступ), строка точности GPS.
 */
defineProps<{
  /** Сила тряски 0…1 — от датчика. */
  intensity: number
  /** Встряска ушла на сервер, ждём пару. */
  sending: boolean
  /** Экран занят другим (например, открывает сбор) — крутилка вместо иконки. */
  busy: boolean
  /** Можно трясти: сбор открыт. */
  active: boolean
  headline: string
  /** Датчик не работает — почему и что делать. */
  sensorProblem: string | null
  position: UserPosition | null
  gpsProblem: string | null
}>()

defineEmits<{ shake: [] }>()
</script>

<template>
  <section class="flex flex-col items-center gap-space-md text-center">
    <div class="relative flex h-56 w-56 items-center justify-center" aria-hidden="true">
      <span
        class="absolute inset-0 rounded-full bg-primary/15 transition-transform duration-100"
        :style="{ transform: `scale(${0.8 + intensity * 0.35})` }"
      />
      <span class="absolute inset-8 rounded-full bg-primary/25" :class="{ 'animate-ping': sending }" />
      <span
        class="relative flex h-32 w-32 items-center justify-center rounded-full"
        :class="active ? 'bg-primary-container text-white shadow-stamp' : 'bg-surface-container-high text-outline shadow-float'"
      >
        <MsIcon :name="sending || busy ? 'progress_activity' : 'vibration'" :size="56" :class="{ 'animate-spin': sending || busy }" />
      </span>
    </div>

    <p class="font-headline-sm text-headline-sm text-on-surface">{{ headline }}</p>

    <p v-if="sensorProblem" class="font-body-sm text-body-sm text-on-surface-variant">{{ sensorProblem }}</p>

    <button
      type="button"
      class="flex items-center gap-1.5 rounded-full bg-secondary px-space-lg py-2.5 font-label-lg text-label-lg text-on-secondary shadow-float transition-transform active:scale-95 disabled:opacity-60"
      :disabled="sending || !active"
      @click="$emit('shake')"
    >
      <MsIcon name="touch_app" :size="20" />
      Встряхнуть
    </button>

    <p class="flex items-center gap-1 font-label-sm text-label-sm text-outline">
      <MsIcon name="my_location" :size="14" />
      <template v-if="position">GPS ± {{ Math.round(position.accuracyMeters) }} м</template>
      <template v-else-if="gpsProblem">{{ gpsProblem }}</template>
      <template v-else>Ищем GPS…</template>
    </p>
  </section>
</template>
