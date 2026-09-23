<script setup lang="ts">
import { formatDateTime } from '@/core/format'
import MsIcon from '@/ui/MsIcon.vue'

import { CLIP_STATUS, type Clip } from '../data'

/** Заявка на «Живое фото» в списке «Мои заявки». */
defineProps<{
  clip: Clip
  active: boolean
  busy: boolean
}>()

defineEmits<{ watch: []; retry: []; share: [] }>()
</script>

<template>
  <article
    class="flex items-center gap-space-sm rounded-DEFAULT p-space-sm shadow-sm transition-colors"
    :class="active ? 'bg-secondary-container/40' : 'bg-surface-container-lowest'"
  >
    <img :src="clip.source_photo_url" alt="" class="h-16 w-12 shrink-0 rounded-md bg-surface-container-high object-cover" />
    <div class="min-w-0 flex-1">
      <h4 class="truncate font-label-lg text-label-lg text-on-surface">{{ clip.soldier_name || 'Без имени' }}</h4>
      <p class="truncate font-body-sm text-body-sm text-on-surface-variant">{{ formatDateTime(clip.created_at) }}</p>
      <span
        class="mt-1 inline-flex items-center gap-1 rounded-full px-2 py-0.5 font-label-sm text-label-sm"
        :class="CLIP_STATUS[clip.status].class"
      >
        <MsIcon :name="CLIP_STATUS[clip.status].icon" :size="13" :class="{ 'animate-spin': clip.status === 'processing' }" />
        {{ CLIP_STATUS[clip.status].title }}
      </span>
      <p v-if="clip.status === 'failed' && clip.error" class="mt-1 font-body-sm text-body-sm text-error">{{ clip.error }}</p>
    </div>
    <div class="flex shrink-0 flex-col gap-1">
      <button
        v-if="clip.status === 'ready'"
        type="button"
        class="flex h-9 w-9 items-center justify-center rounded-full bg-primary text-on-primary"
        aria-label="Смотреть"
        @click="$emit('watch')"
      >
        <MsIcon name="play_arrow" :size="20" filled />
      </button>
      <button
        v-if="clip.status === 'ready'"
        type="button"
        class="flex h-9 w-9 items-center justify-center rounded-full bg-secondary-container text-on-secondary-container"
        aria-label="Отправить родным"
        @click="$emit('share')"
      >
        <MsIcon name="send" :size="18" />
      </button>
      <button
        v-if="clip.status === 'failed'"
        type="button"
        class="flex h-9 w-9 items-center justify-center rounded-full bg-surface-container-high text-on-surface disabled:opacity-60"
        aria-label="Повторить"
        :disabled="busy"
        @click="$emit('retry')"
      >
        <MsIcon :name="busy ? 'progress_activity' : 'refresh'" :size="18" :class="{ 'animate-spin': busy }" />
      </button>
    </div>
  </article>
</template>
