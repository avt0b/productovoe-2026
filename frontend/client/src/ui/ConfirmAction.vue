<script setup lang="ts">
import { ref } from 'vue'

import MsIcon from './MsIcon.vue'

/**
 * Необратимое действие в два нажатия: первое раскрывает подтверждение с
 * пояснением, второе — делает. Случайный тап по «Удалить» не должен стоить
 * отряду выезда. В слот кладут то, что нужно спросить заодно, — например,
 * причину отмены.
 */
withDefaults(
  defineProps<{
    label: string
    icon: string
    /** Что именно произойдёт — без этого подтверждение превращается в формальность. */
    warning: string
    confirmLabel: string
    busy?: boolean
    /** `danger` — удаление, `neutral` — отмена, после которой что-то остаётся. */
    tone?: 'danger' | 'neutral'
  }>(),
  { busy: false, tone: 'danger' },
)

const emit = defineEmits<{ confirm: [] }>()

const open = ref(false)
</script>

<template>
  <div class="flex flex-col">
    <button
      type="button"
      class="flex items-center gap-space-xs self-center rounded-full px-space-md py-2 font-label-md text-label-md active:scale-95"
      :class="tone === 'danger' ? 'text-error' : 'text-on-surface-variant'"
      :aria-expanded="open"
      @click="open = !open"
    >
      <MsIcon :name="icon" :size="18" />
      {{ label }}
    </button>
    <div
      class="grid transition-[grid-template-rows,opacity] duration-300 ease-out"
      :class="open ? 'grid-rows-[1fr] opacity-100' : 'grid-rows-[0fr] opacity-0'"
      :inert="!open"
    >
      <div class="overflow-hidden">
        <div
          class="mt-space-xs flex flex-col gap-space-sm rounded-2xl p-space-md"
          :class="tone === 'danger' ? 'bg-error-container' : 'bg-surface-container-low'"
          role="alertdialog"
          :aria-label="label"
        >
          <p class="font-body-sm text-body-sm" :class="tone === 'danger' ? 'text-on-error-container' : 'text-on-surface'">
            {{ warning }}
          </p>
          <slot />
          <div class="flex gap-space-sm">
            <button
              type="button"
              class="flex-1 rounded-full bg-surface-container-lowest py-2.5 font-label-md text-label-md text-on-surface active:scale-95"
              @click="open = false"
            >
              Оставить
            </button>
            <button
              type="button"
              class="flex flex-1 items-center justify-center gap-1.5 rounded-full py-2.5 font-label-md text-label-md active:scale-95 disabled:opacity-60"
              :class="tone === 'danger' ? 'bg-error text-on-error' : 'bg-secondary text-on-secondary'"
              :disabled="busy"
              @click="emit('confirm')"
            >
              <MsIcon :name="busy ? 'progress_activity' : icon" :size="18" :class="{ 'animate-spin': busy }" />
              {{ confirmLabel }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
