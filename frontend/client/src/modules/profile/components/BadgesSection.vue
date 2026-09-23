<script setup lang="ts">
import { computed } from 'vue'

import MsIcon from '@/ui/MsIcon.vue'

import type { Achievement } from '../api'
import { describeAchievement, formatDate } from '../data'

const props = defineProps<{ achievements: Achievement[] }>()

/** Свежие сверху: бэкенд отдаёт в порядке выдачи, а не по дате. */
const items = computed(() =>
  [...props.achievements]
    .map(describeAchievement)
    .sort((a, b) => b.earnedAt.localeCompare(a.earnedAt)),
)
</script>

<template>
  <section class="flex flex-col gap-space-sm">
    <div class="flex items-center gap-space-xs px-1">
      <MsIcon name="workspace_premium" :size="20" class="text-tertiary" />
      <h3 class="font-headline-sm text-headline-sm text-on-surface">Отличия</h3>
      <span v-if="items.length" class="font-label-sm text-label-sm text-on-surface-variant">{{ items.length }}</span>
    </div>

    <!--
      Пусто — обычное состояние нового исследователя, а не ошибка: отличия
      выдают другие сервисы за пройденный маршрут, выезд, сбор и проверку
      записи в архиве.
    -->
    <p
      v-if="!items.length"
      class="rounded-DEFAULT bg-surface-container-lowest p-space-md font-body-sm text-body-sm text-on-surface-variant shadow-sm"
    >
      Отличий пока нет. Они появятся за пройденный маршрут, участие в выезде, поддержку сбора и проверенную запись
      в народном архиве.
    </p>

    <ul v-else class="flex flex-col gap-space-xs">
      <li
        v-for="item in items"
        :key="item.code"
        class="flex items-center gap-space-sm rounded-DEFAULT bg-surface-container-lowest p-space-sm shadow-sm"
      >
        <div class="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-tertiary-fixed text-tertiary">
          <MsIcon :name="item.icon" :size="20" filled />
        </div>
        <div class="flex min-w-0 flex-col">
          <span class="break-words font-label-md text-label-md text-on-surface">{{ item.title }}</span>
          <span class="break-words font-body-sm text-body-sm text-on-surface-variant">{{ item.hint }}</span>
        </div>
        <span class="ml-auto shrink-0 font-label-sm text-label-sm text-outline">{{ formatDate(item.earnedAt) }}</span>
      </li>
    </ul>
  </section>
</template>
