<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'

import MsIcon from './MsIcon.vue'

/**
 * Окно поверх экрана: снизу на телефоне, по центру на широком экране.
 *
 * Для коротких форм — взнос, новая точка, заявка. Закрывается крестиком,
 * тапом мимо окна и клавишей Esc.
 */
defineProps<{
  title: string
  subtitle?: string
}>()

const emit = defineEmits<{ close: [] }>()

const closeButton = ref<HTMLButtonElement | null>(null)

function onKey(event: KeyboardEvent): void {
  if (event.key === 'Escape') emit('close')
}

// Фокус внутрь окна: иначе с клавиатуры и скринридером до формы не добраться, не пройдя экран под ним.
onMounted(() => {
  closeButton.value?.focus()
  window.addEventListener('keydown', onKey)
  document.body.style.overflow = 'hidden'
})
onBeforeUnmount(() => {
  window.removeEventListener('keydown', onKey)
  document.body.style.overflow = ''
})
</script>

<template>
  <!-- В body: у каркаса экрана есть размытие фона, внутри него fixed отсчитывался бы от каркаса, а не от окна. -->
  <Teleport to="body">
  <div
    class="fixed inset-0 z-[60] flex items-end justify-center bg-inverse-surface/60 backdrop-blur-sm sm:items-center sm:p-margin"
    role="dialog"
    aria-modal="true"
    :aria-label="title"
    @click.self="emit('close')"
  >
    <div
      class="pb-safe flex max-h-[92vh] w-full max-w-app flex-col overflow-hidden rounded-t-sheet bg-surface-container-lowest shadow-sheet sm:rounded-sheet"
    >
      <!-- «Ручка»: показывает, что окно выезжает снизу, и куда тянуть, чтобы его закрыть. -->
      <div class="flex justify-center pt-space-sm sm:hidden" aria-hidden="true">
        <span class="h-1 w-10 rounded-full bg-outline-variant" />
      </div>
      <div class="flex items-start justify-between gap-space-sm px-space-md pb-space-sm pt-space-md">
        <div class="min-w-0">
          <h3 class="font-headline-sm text-headline-sm text-on-surface">{{ title }}</h3>
          <p v-if="subtitle" class="mt-0.5 font-body-sm text-body-sm text-on-surface-variant">{{ subtitle }}</p>
        </div>
        <button
          ref="closeButton"
          type="button"
          aria-label="Закрыть"
          class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full text-on-surface-variant hover:bg-surface-container"
          @click="emit('close')"
        >
          <MsIcon name="close" :size="22" />
        </button>
      </div>
      <div class="overflow-y-auto px-space-md" :class="$slots.footer ? 'pb-space-sm' : 'pb-space-lg'">
        <slot />
      </div>
      <!-- Низ окна, который не уезжает при прокрутке: поле ввода чата, кнопки формы. -->
      <div v-if="$slots.footer" class="shrink-0 border-t border-outline-variant/40 px-space-md pb-space-md pt-space-sm">
        <slot name="footer" />
      </div>
    </div>
  </div>
  </Teleport>
</template>
