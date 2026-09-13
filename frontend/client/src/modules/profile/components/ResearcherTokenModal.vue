<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'

import type { SessionUser } from '@/core/session'
import MsIcon from '@/ui/MsIcon.vue'

defineProps<{ user: SessionUser }>()

const emit = defineEmits<{ close: [] }>()

const closeButton = ref<HTMLButtonElement | null>(null)

function onKey(event: KeyboardEvent): void {
  if (event.key === 'Escape') emit('close')
}

// Фокус на «Закрыть»: иначе с клавиатуры и скринридером окно не закрыть, не пройдя весь профиль под ним.
onMounted(() => {
  closeButton.value?.focus()
  window.addEventListener('keydown', onKey)
})
onBeforeUnmount(() => window.removeEventListener('keydown', onKey))

/** Короткая подпись жетона: «Смирнов К.» из «Константин Смирнов». */
function shortName(name: string): string {
  const [first, last] = name.split(' ')
  return last ? `${last} ${first[0]}.` : name
}
</script>

<template>
  <div
    class="fixed inset-0 z-[60] flex items-center justify-center bg-inverse-surface/60 p-margin backdrop-blur-sm"
    role="dialog"
    aria-modal="true"
    aria-label="Цифровой жетон исследователя"
    @click.self="emit('close')"
  >
    <div class="flex w-full max-w-sm flex-col items-center gap-space-md rounded-lg bg-surface-container-lowest p-space-lg text-center shadow-2xl">
      <div class="flex h-12 w-12 items-center justify-center rounded-full bg-secondary-fixed text-secondary">
        <MsIcon name="badge" :size="28" />
      </div>
      <div>
        <h3 class="font-headline-sm text-headline-sm text-on-surface">Цифровой жетон исследователя</h3>
        <p class="mt-1 font-body-sm text-body-sm text-on-surface-variant">
          Предъявите куратору или на контрольной точке мемориала для фиксации маршрута.
        </p>
      </div>

      <div class="flex flex-col items-center rounded-DEFAULT bg-surface-container p-space-md">
        <!-- Условный QR из макета. Настоящий код с подписью сессии выдаст `user_service`. -->
        <div class="flex h-44 w-44 items-center justify-center rounded-DEFAULT bg-surface-container-lowest p-2 shadow-inner">
          <svg class="h-full w-full text-secondary" fill="currentColor" viewBox="0 0 100 100" aria-hidden="true">
            <path d="M10,10 h30 v30 h-30 z M15,15 v20 h20 v-20 z M20,20 h10 v10 h-10 z" />
            <path d="M60,10 h30 v30 h-30 z M65,15 v20 h20 v-20 z M70,20 h10 v10 h-10 z" />
            <path d="M10,60 h30 v30 h-30 z M15,65 v20 h20 v-20 z M20,70 h10 v10 h-10 z" />
            <circle cx="50" cy="50" r="8" />
            <rect x="55" y="60" width="10" height="10" />
            <rect x="75" y="60" width="15" height="10" />
            <rect x="55" y="80" width="20" height="10" />
            <rect x="80" y="75" width="10" height="15" />
          </svg>
        </div>
        <span class="mt-2 font-label-sm text-label-sm text-on-surface-variant">#{{ user.id }} • {{ shortName(user.name) }}</span>
      </div>

      <button
        ref="closeButton"
        type="button"
        class="w-full rounded-full bg-secondary py-3 font-label-lg text-label-lg text-on-secondary shadow-sm"
        @click="emit('close')"
      >
        Закрыть жетон
      </button>
    </div>
  </div>
</template>
