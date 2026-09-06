<script setup lang="ts">
import { onBeforeUnmount, onMounted } from 'vue'

withDefaults(
  defineProps<{ title: string; icon?: string; tone?: 'primary' | 'danger'; busy?: boolean }>(),
  { icon: 'edit', tone: 'primary', busy: false },
)

const emit = defineEmits<{ close: [] }>()

function onKeydown(event: KeyboardEvent): void {
  if (event.key === 'Escape') emit('close')
}

onMounted(() => document.addEventListener('keydown', onKeydown))
onBeforeUnmount(() => document.removeEventListener('keydown', onKeydown))
</script>

<template>
  <div
    class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-space-4 backdrop-blur-sm"
    role="dialog"
    aria-modal="true"
    @click.self="emit('close')"
  >
    <div class="flex w-full max-w-xl flex-col gap-space-4 rounded-xl bg-surface-container-low p-space-6 shadow-xl">
      <div class="flex items-center justify-between gap-space-3 pb-space-2">
        <div
          class="flex items-center gap-space-2"
          :class="tone === 'danger' ? 'text-error' : 'text-primary'"
        >
          <span class="ms-icon text-[24px]">{{ icon }}</span>
          <span class="font-headline-sm text-headline-sm uppercase">{{ title }}</span>
        </div>
        <button
          class="rounded p-1 text-on-surface-variant hover:bg-surface-container hover:text-on-surface"
          type="button"
          aria-label="Закрыть"
          @click="emit('close')"
        >
          <span class="ms-icon">close</span>
        </button>
      </div>

      <slot />

      <div class="flex items-center justify-end gap-space-3 pt-space-2">
        <button class="btn-secondary" type="button" :disabled="busy" @click="emit('close')">
          Отмена
        </button>
        <slot name="actions" />
      </div>
    </div>
  </div>
</template>
