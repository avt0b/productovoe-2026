<script setup lang="ts">
import MsIcon from '@/ui/MsIcon.vue'

/**
 * Подсказка под кнопкой AR: что искать на местности и что ответил AR-экран
 * (нашли метку, вышли, камера недоступна).
 */
defineProps<{
  /** Подсказка автора точки: «след кабельного окопа за берёзой». */
  hint: string
  /** Чем закончился прошлый запуск. `null` — ещё не запускали. */
  note: string | null
}>()
</script>

<template>
  <div
    class="flex items-start gap-space-sm rounded-DEFAULT bg-tertiary-fixed/40 px-space-sm py-2 font-body-sm text-body-sm text-on-tertiary-fixed-variant"
    role="status"
  >
    <MsIcon name="smartphone" :size="18" class="mt-0.5 shrink-0" />
    <p>
      {{ hint }}
      <span v-if="note" class="block pt-1 opacity-80">{{ note }}</span>
    </p>
  </div>
</template>
