<script setup lang="ts">
import { onBeforeUnmount, ref } from 'vue'

import MsIcon from '@/ui/MsIcon.vue'

import type { FindRecord } from '../data'

defineProps<{ record: FindRecord }>()

/** Сколько держать подтверждение на кнопке, прежде чем вернуть исходную надпись. */
const FEEDBACK_MS = 3000

const volunteered = ref(false)
const openingForm = ref(false)
let volunteerTimer: ReturnType<typeof setTimeout> | undefined
let formTimer: ReturnType<typeof setTimeout> | undefined

/** Заявки пока никуда не уходят — кнопка показывает, что нажатие принято. */
function volunteer(): void {
  volunteered.value = true
  clearTimeout(volunteerTimer)
  volunteerTimer = setTimeout(() => (volunteered.value = false), FEEDBACK_MS)
}

function addData(): void {
  openingForm.value = true
  clearTimeout(formTimer)
  formTimer = setTimeout(() => (openingForm.value = false), FEEDBACK_MS - 1000)
}

onBeforeUnmount(() => {
  clearTimeout(volunteerTimer)
  clearTimeout(formTimer)
})
</script>

<template>
  <div class="flex flex-col space-y-space-md rounded-lg bg-surface-container-lowest p-space-md shadow-md">
    <div class="flex flex-wrap items-center justify-between gap-space-xs">
      <span class="inline-flex items-center gap-1.5 rounded-full bg-tertiary-fixed px-3 py-1 font-label-md text-label-md text-on-tertiary-fixed">
        <MsIcon name="timelapse" :size="14" />
        {{ record.stage }}
      </span>
      <span class="rounded-full bg-surface-container-high px-2.5 py-1 font-label-sm text-label-sm text-on-surface-variant">
        {{ record.square }}
      </span>
    </div>

    <div>
      <h3 class="font-headline-lg-mobile text-headline-lg-mobile leading-tight text-on-surface">{{ record.title }}</h3>
      <p class="mt-1 font-body-md text-body-md text-outline">{{ record.period }}</p>
    </div>

    <div v-if="record.photos.length" class="grid grid-cols-2 gap-space-sm">
      <div v-for="photo in record.photos" :key="photo.src" class="relative h-28 overflow-hidden rounded-lg shadow-sm">
        <img :src="photo.src" :alt="photo.caption" class="h-full w-full object-cover" />
        <div class="absolute bottom-1.5 left-2 rounded-full bg-inverse-surface/75 px-2 py-0.5 font-label-sm text-label-sm text-inverse-on-surface">
          {{ photo.caption }}
        </div>
      </div>
    </div>

    <div class="space-y-space-xs rounded-lg bg-surface-container-low p-space-md">
      <div class="flex items-start gap-2 text-on-surface-variant">
        <MsIcon name="pin_drop" :size="18" class="mt-0.5 shrink-0 text-primary" />
        <span class="select-all font-body-sm text-body-sm">{{ record.coordinates }}</span>
      </div>
      <div class="flex items-start gap-2 pt-1 text-on-surface-variant">
        <MsIcon name="menu_book" :size="18" class="mt-0.5 shrink-0 text-secondary" />
        <span class="font-body-sm text-body-sm">{{ record.source }}</span>
      </div>
      <div class="flex items-start gap-2 pt-1 text-on-surface-variant">
        <MsIcon name="verified" :size="18" class="mt-0.5 shrink-0 text-tertiary" />
        <span class="font-body-sm text-body-sm leading-snug">{{ record.evidence }}</span>
      </div>
    </div>

    <div class="flex flex-col gap-space-sm pt-1 sm:flex-row">
      <button
        type="button"
        class="flex flex-1 items-center justify-center gap-1.5 rounded-full px-space-md py-3 font-label-lg text-label-lg shadow-md transition-transform hover:opacity-95 active:scale-95"
        :class="volunteered ? 'bg-secondary text-on-secondary' : 'bg-primary text-on-primary'"
        @click="volunteer"
      >
        <MsIcon :name="volunteered ? 'check' : 'handshake'" :size="20" />
        <span>{{ volunteered ? 'Заявка принята!' : 'Я готов помочь в выезде' }}</span>
      </button>
      <button
        type="button"
        class="flex flex-1 items-center justify-center gap-1.5 rounded-full bg-secondary-container px-space-md py-3 font-label-lg text-label-lg text-on-secondary-container transition-transform hover:opacity-90 active:scale-95"
        @click="addData"
      >
        <MsIcon :name="openingForm ? 'folder_open' : 'upload_file'" :size="20" />
        <span>{{ openingForm ? 'Открытие формы...' : 'Дополнить данными' }}</span>
      </button>
    </div>
  </div>
</template>
