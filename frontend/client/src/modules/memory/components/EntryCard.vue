<script setup lang="ts">
import { ref } from 'vue'

import { formatCoordinates } from '@/core/geo'
import MsIcon from '@/ui/MsIcon.vue'

import { ENTRY_KINDS, ENTRY_STATUS, type ArchiveEntry } from '../data'

/**
 * Запись народного архива. `mine` — своя запись: видно, на какой она стадии и
 * что написал проверяющий. `reviewable` — краевед проверяет чужую запись.
 */
const props = defineProps<{
  entry: ArchiveEntry
  mine?: boolean
  reviewable?: boolean
  busy?: boolean
}>()

const emit = defineEmits<{ review: [verdict: 'verify' | 'reject', note: string] }>()

const expanded = ref(false)
const rejecting = ref(false)
const note = ref('')

function confirmReject(): void {
  emit('review', 'reject', note.value.trim())
}

const longBody = props.entry.body.length > 220
</script>

<template>
  <article class="flex flex-col gap-space-sm rounded-DEFAULT bg-surface-container-lowest p-space-md shadow-sm">
    <div class="flex items-center justify-between gap-space-xs">
      <span class="inline-flex items-center gap-1 font-label-sm text-label-sm uppercase tracking-wider text-outline">
        <MsIcon :name="ENTRY_KINDS[entry.kind].icon" :size="15" />
        {{ ENTRY_KINDS[entry.kind].title }}
      </span>
      <span
        v-if="mine || reviewable || entry.status === 'verified'"
        class="inline-flex items-center gap-1 rounded-full px-2 py-0.5 font-label-sm text-label-sm"
        :class="ENTRY_STATUS[entry.status].class"
      >
        <MsIcon :name="ENTRY_STATUS[entry.status].icon" :size="13" :filled="entry.status === 'verified'" />
        {{ ENTRY_STATUS[entry.status].title }}
      </span>
    </div>

    <div>
      <h4 class="font-headline-sm text-headline-sm leading-tight text-on-surface">{{ entry.title }}</h4>
      <p v-if="entry.date_text" class="mt-0.5 font-label-md text-label-md text-primary">{{ entry.date_text }}</p>
    </div>

    <p
      v-if="entry.body"
      class="whitespace-pre-line font-body-sm text-body-sm text-on-surface-variant"
      :class="{ 'line-clamp-4': longBody && !expanded }"
    >
      {{ entry.body }}
    </p>
    <button
      v-if="longBody"
      type="button"
      class="self-start font-label-md text-label-md text-primary"
      @click="expanded = !expanded"
    >
      {{ expanded ? 'Свернуть' : 'Читать полностью' }}
    </button>

    <img v-if="entry.media_url" :src="entry.media_url" alt="" class="max-h-56 w-full rounded-DEFAULT object-cover" />

    <p v-if="entry.lat !== null && entry.lon !== null" class="flex items-center gap-1 font-body-sm text-body-sm text-outline">
      <MsIcon name="pin_drop" :size="15" />
      {{ formatCoordinates({ lat: entry.lat, lon: entry.lon }) }}
    </p>

    <p
      v-if="mine && entry.review_note"
      class="rounded-DEFAULT bg-surface-container-low px-3 py-2 font-body-sm text-body-sm text-on-surface-variant"
    >
      Комментарий проверяющего: {{ entry.review_note }}
    </p>

    <template v-if="reviewable">
      <div v-if="!rejecting" class="grid grid-cols-2 gap-space-sm pt-space-xs">
        <button
          type="button"
          class="flex items-center justify-center gap-1.5 rounded-full bg-secondary py-2.5 font-label-md text-label-md text-on-secondary disabled:opacity-60"
          :disabled="busy"
          @click="emit('review', 'verify', '')"
        >
          <MsIcon :name="busy ? 'progress_activity' : 'verified'" :size="18" :class="{ 'animate-spin': busy }" />
          Подтвердить
        </button>
        <button
          type="button"
          class="flex items-center justify-center gap-1.5 rounded-full bg-surface-container-high py-2.5 font-label-md text-label-md text-on-surface disabled:opacity-60"
          :disabled="busy"
          @click="rejecting = true"
        >
          <MsIcon name="block" :size="18" />
          Отклонить
        </button>
      </div>
      <form v-else class="flex flex-col gap-space-xs pt-space-xs" @submit.prevent="confirmReject">
        <label class="sr-only" :for="`note-${entry.id}`">Почему отклонено</label>
        <textarea
          :id="`note-${entry.id}`"
          v-model="note"
          rows="2"
          maxlength="1000"
          placeholder="Почему: не нашли в Книге Памяти, нужны документы…"
          class="w-full rounded-DEFAULT bg-surface-container-low px-3 py-2 font-body-sm text-body-sm text-on-surface outline-none focus:ring-2 focus:ring-primary"
        />
        <div class="grid grid-cols-2 gap-space-sm">
          <button type="button" class="rounded-full bg-surface-container-high py-2.5 font-label-md text-label-md" @click="rejecting = false">
            Назад
          </button>
          <button
            type="submit"
            class="rounded-full bg-error py-2.5 font-label-md text-label-md text-on-error disabled:opacity-60"
            :disabled="busy"
          >
            Отклонить
          </button>
        </div>
      </form>
    </template>
  </article>
</template>
