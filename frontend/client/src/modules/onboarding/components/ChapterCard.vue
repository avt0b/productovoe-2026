<script setup lang="ts">
import { ref } from 'vue'

import MsIcon from '@/ui/MsIcon.vue'

import type { Chapter } from '../data'

/**
 * Глава обучения в шпаргалке: строка «что здесь делают» и, если развернуть, —
 * из чего она состоит. Свёрнутый вид держит всю шпаргалку на одном экране:
 * восемь раскрытых карточек читать никто не станет.
 *
 * Шаги показаны заголовками, а не пересказом: подробности — в самом обучении,
 * и отсюда в него ведёт «Пройти главу». Иначе одно и то же пришлось бы
 * поддерживать в двух местах и они бы разошлись.
 */
defineProps<{
  chapter: Chapter
  /** Раздел есть в сборке — можно вести. `false` — только текст. */
  openable: boolean
}>()

const emit = defineEmits<{ play: []; open: [] }>()

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
        <MsIcon :name="chapter.icon" :size="20" />
      </span>
      <span class="min-w-0 flex-1">
        <span class="block font-headline-sm text-headline-sm text-on-surface">{{ chapter.title }}</span>
        <span class="block font-body-sm text-body-sm text-on-surface-variant">{{ chapter.summary }}</span>
      </span>
      <span class="shrink-0 font-label-sm text-label-sm text-outline">{{ chapter.steps.length }}</span>
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
          <li
            v-for="step in chapter.steps"
            :key="step.id"
            class="flex items-center gap-space-sm font-body-sm text-body-sm text-on-surface"
          >
            <MsIcon :name="step.icon" :size="18" class="shrink-0 text-outline" />
            <span class="min-w-0">{{ step.title }}</span>
          </li>
        </ul>

        <div class="mt-space-sm flex flex-wrap gap-space-xs">
          <button
            type="button"
            class="flex min-h-11 items-center gap-space-xs rounded-full bg-primary-container px-space-md py-2 font-label-md text-label-md text-white shadow-stamp transition-colors hover:bg-primary active:scale-95"
            @click="emit('play')"
          >
            <MsIcon name="play_arrow" :size="18" />
            Пройти главу
          </button>
          <button
            v-if="openable"
            type="button"
            class="min-h-11 rounded-full bg-surface-container-high px-space-md py-2 font-label-md text-label-md text-on-surface active:scale-95"
            @click="emit('open')"
          >
            Открыть раздел
          </button>
        </div>
      </div>
    </div>
  </section>
</template>
