<script setup lang="ts">
import { ref } from 'vue'

import MsIcon from '@/ui/MsIcon.vue'

/**
 * Раздел приложения: строка «что здесь делают» и, если развернуть, — из чего
 * он состоит. Свёрнутый вид держит всю шпаргалку на одном экране: шесть
 * раскрытых карточек читать никто не станет.
 */
defineProps<{
  icon: string
  title: string
  summary: string
  lines: string[]
  /** Раздел есть в сборке — можно вести. `false` — только текст. */
  openable: boolean
}>()

const emit = defineEmits<{ open: [] }>()

const open = ref(false)
</script>

<template>
  <section class="flex flex-col rounded-2xl bg-surface-container-lowest p-space-md shadow-document">
    <button
      type="button"
      class="flex min-h-11 items-center gap-space-sm text-left"
      :aria-expanded="open"
      @click="open = !open"
    >
      <span
        class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-secondary-container text-on-secondary-container"
        aria-hidden="true"
      >
        <MsIcon :name="icon" :size="20" />
      </span>
      <span class="min-w-0 flex-1">
        <span class="block font-headline-sm text-headline-sm text-on-surface">{{ title }}</span>
        <span class="block font-body-sm text-body-sm text-on-surface-variant">{{ summary }}</span>
      </span>
      <MsIcon
        name="expand_more"
        :size="22"
        class="shrink-0 text-on-surface-variant transition-transform duration-300"
        :class="{ 'rotate-180': open }"
      />
    </button>

    <!-- Раскрывается, а не появляется: карточки ниже не должны прыгать. -->
    <div
      class="grid transition-[grid-template-rows,opacity] duration-300 ease-out"
      :class="open ? 'grid-rows-[1fr] opacity-100' : 'grid-rows-[0fr] opacity-0'"
      :inert="!open"
    >
      <div class="overflow-hidden">
        <ul class="mt-space-sm flex flex-col gap-space-xs">
          <li v-for="line in lines" :key="line" class="flex gap-space-xs font-body-sm text-body-sm text-on-surface">
            <MsIcon name="chevron_right" :size="18" class="mt-0.5 shrink-0 text-outline" />
            <span>{{ line }}</span>
          </li>
        </ul>
        <button
          v-if="openable"
          type="button"
          class="mt-space-sm min-h-11 rounded-full bg-surface-container-high px-space-md py-2 font-label-md text-label-md text-on-surface active:scale-95"
          @click="emit('open')"
        >
          Открыть раздел
        </button>
      </div>
    </div>
  </section>
</template>
