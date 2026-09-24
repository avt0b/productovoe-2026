<script setup lang="ts">
import MsIcon from '@/ui/MsIcon.vue'

import { PLACE_KINDS, type MapPlace } from '../data'

defineProps<{
  place: MapPlace
  /** Расстояние от человека, если известно, где он. */
  distance: string | null
  /** Место добавил этот человек (или он администратор) — его можно поправить и убрать. */
  canEdit: boolean
}>()

defineEmits<{ close: []; edit: [] }>()
</script>

<template>
  <article class="flex flex-col gap-space-xs rounded-2xl bg-surface-container-lowest p-space-md shadow-document">
    <div class="flex items-start justify-between gap-space-sm">
      <span
        class="inline-flex items-center gap-1.5 rounded-full bg-surface-container-high px-2.5 py-1 font-archival text-archival uppercase text-on-surface-variant"
      >
        <MsIcon :name="PLACE_KINDS[place.kind].icon" :size="14" />
        {{ PLACE_KINDS[place.kind].title }}
      </span>
      <button
        type="button"
        aria-label="Закрыть карточку"
        class="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-surface-container-low text-on-surface-variant transition-colors hover:text-on-surface"
        @click="$emit('close')"
      >
        <MsIcon name="close" :size="18" />
      </button>
    </div>

    <h3 class="font-headline-sm text-headline-sm text-on-surface">{{ place.title }}</h3>

    <p
      v-if="place.dateText || distance"
      class="flex flex-wrap items-center gap-x-space-sm font-label-md text-label-md text-outline"
    >
      <span v-if="place.dateText" class="inline-flex items-center gap-1">
        <MsIcon name="event" :size="15" />
        {{ place.dateText }}
      </span>
      <span v-if="distance" class="inline-flex items-center gap-1">
        <MsIcon name="near_me" :size="15" />
        {{ distance }} от вас
      </span>
    </p>

    <p class="font-body-sm text-body-sm leading-relaxed text-on-surface-variant">{{ place.description }}</p>

    <p v-if="place.source" class="flex items-start gap-1.5 font-body-sm text-body-sm text-outline">
      <MsIcon name="menu_book" :size="16" class="mt-0.5 shrink-0" />
      <span>{{ place.source }}</span>
    </p>

    <button
      v-if="canEdit"
      type="button"
      class="mt-space-xs flex items-center gap-space-xs self-start rounded-full bg-surface-container-high px-space-md py-2 font-label-md text-label-md text-on-surface active:scale-95"
      @click="$emit('edit')"
    >
      <MsIcon name="edit" :size="18" />
      Поправить место
    </button>
  </article>
</template>
