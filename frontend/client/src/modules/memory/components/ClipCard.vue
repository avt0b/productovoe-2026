<script setup lang="ts">
import { computed } from 'vue'

import { formatDateTime } from '@/core/format'
import MsIcon from '@/ui/MsIcon.vue'

import { CLIP_STATUS, type Clip } from '../data'

/** Заявка на «Живое фото» в семейном архиве. */
const props = defineProps<{
  clip: Clip
  active: boolean
  busy: boolean
}>()

defineEmits<{ watch: []; retry: []; share: [] }>()

const waiting = computed(() => props.clip.status === 'queued' || props.clip.status === 'processing')
</script>

<template>
  <article
    class="flex flex-col gap-space-sm rounded-2xl p-space-sm transition-colors duration-200"
    :class="active ? 'bg-surface-container-lowest shadow-document ring-2 ring-secondary/50' : 'bg-surface-container-lowest shadow-document'"
  >
    <div class="flex items-center gap-space-sm">
      <img :src="clip.source_photo_url" alt="" class="h-16 w-12 shrink-0 rounded-DEFAULT bg-surface-container-high object-cover" loading="lazy" />
      <div class="flex min-w-0 flex-1 flex-col gap-0.5">
        <h3 class="truncate font-label-lg text-label-lg text-on-surface">{{ clip.soldier_name || 'Без имени' }}</h3>
        <p class="flex items-center gap-1 truncate font-body-sm text-body-sm text-on-surface-variant">
          <MsIcon :name="clip.is_public ? 'public' : 'lock'" :size="15" class="shrink-0" />
          {{ clip.is_public ? 'В общем мемориале' : 'Только семья' }} · {{ formatDateTime(clip.created_at) }}
        </p>
        <span
          class="flex items-center gap-1 self-start rounded-full px-2 py-0.5 font-label-sm text-label-sm"
          :class="CLIP_STATUS[clip.status].class"
        >
          <MsIcon :name="CLIP_STATUS[clip.status].icon" :size="15" :class="{ 'animate-spin': clip.status === 'processing' }" />
          {{ CLIP_STATUS[clip.status].title }}
        </span>
      </div>
      <div class="flex shrink-0 gap-space-xs">
        <template v-if="clip.status === 'ready'">
          <button
            type="button"
            class="flex h-10 w-10 items-center justify-center rounded-full bg-secondary text-on-secondary active:scale-95"
            :aria-label="`Смотреть: ${clip.soldier_name || 'без имени'}`"
            :aria-pressed="active"
            @click="$emit('watch')"
          >
            <MsIcon name="play_arrow" :size="20" filled />
          </button>
          <button
            type="button"
            class="flex h-10 w-10 items-center justify-center rounded-full bg-surface-container-high text-on-surface active:scale-95"
            aria-label="Отправить родным"
            @click="$emit('share')"
          >
            <MsIcon name="send" :size="18" />
          </button>
        </template>
        <button
          v-else-if="clip.status === 'failed'"
          type="button"
          class="flex h-10 w-10 items-center justify-center rounded-full bg-surface-container-high text-on-surface active:scale-95 disabled:opacity-60"
          aria-label="Повторить оживление"
          :disabled="busy"
          @click="$emit('retry')"
        >
          <MsIcon :name="busy ? 'progress_activity' : 'refresh'" :size="18" :class="{ 'animate-spin': busy }" />
        </button>
      </div>
    </div>

    <!-- Ждать приходится минуты: полоска показывает, что заявка жива, а экран обновит статус сам. -->
    <div v-if="waiting" class="flex flex-col gap-1">
      <div class="h-1 w-full overflow-hidden rounded-full bg-surface-container-high" aria-hidden="true">
        <div class="h-full w-full rounded-full bg-secondary/60 motion-safe:animate-pulse" />
      </div>
      <p class="font-body-sm text-body-sm text-on-surface-variant" role="status">
        {{ clip.status === 'queued' ? 'Ждёт очереди на оживление' : 'Оживляем портрет' }} — статус обновится сам
      </p>
    </div>
    <p v-if="clip.status === 'failed' && clip.error" class="font-body-sm text-body-sm text-error">{{ clip.error }}</p>
  </article>
</template>
