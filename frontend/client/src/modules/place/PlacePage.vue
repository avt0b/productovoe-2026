<script setup lang="ts">
import { computed } from 'vue'

import { useAsync } from '@/core/async'
import { usePreferencesStore } from '@/core/preferences'
import type { PoiKind } from '@/core/services/map'
import DemoDataBadge from '@/ui/DemoDataBadge.vue'
import InlineNotice from '@/ui/InlineNotice.vue'
import MsIcon from '@/ui/MsIcon.vue'
import StateBlock from '@/ui/StateBlock.vue'

import PhotoPuzzle from './components/PhotoPuzzle.vue'
import { fetchPlace } from './data'

const props = defineProps<{ poiId: string }>()

const preferences = usePreferencesStore()
const { data: place, loading, error, retry } = useAsync(() => fetchPlace(props.poiId))

const KIND_TITLES: Record<PoiKind, string> = {
  grave: 'Братская могила',
  battle: 'Место боя',
  monument: 'Памятник',
  hospital: 'Госпиталь',
  trench: 'Рубеж обороны',
  airfield: 'Аэродром',
  other: 'Памятное место',
}

const kindTitle = computed(() => (place.value ? KIND_TITLES[place.value.kind] : ''))
</script>

<template>
  <div class="flex w-full flex-col gap-space-md px-margin pb-space-xl pt-space-xs">
    <StateBlock v-if="loading || error" :loading="loading" :error="error" class="mt-space-md" @retry="retry" />

    <template v-else-if="place">
      <DemoDataBadge v-if="place.source === 'demo'" />

      <div class="flex flex-col gap-space-xs">
        <p class="flex items-center gap-1.5 font-label-md text-label-md text-secondary">
          <MsIcon name="nfc" :size="16" />
          <span>{{ kindTitle }} · по метке рядом</span>
        </p>
        <h2
          class="ribbon-shimmer font-headline-lg-mobile text-headline-lg-mobile text-on-surface [--shimmer-base:theme(colors.ink.DEFAULT)]"
        >
          {{ place.title }}
        </h2>
        <p v-if="place.dateText" class="flex items-center gap-1.5 font-body-md text-body-md text-on-surface-variant">
          <MsIcon name="event" :size="18" class="text-secondary" />
          <span>{{ place.dateText }}</span>
        </p>
      </div>

      <!-- Детский режим — мини-игра: собрать фотографию места из пазла -->
      <div
        v-if="preferences.familyMode"
        class="flex flex-col gap-space-sm rounded-2xl bg-surface-container-lowest p-space-md shadow-document"
      >
        <div class="flex items-center gap-space-xs text-on-surface-variant">
          <MsIcon name="extension" :size="18" class="text-primary" />
          <h4 class="font-archival text-archival uppercase">Собери фотографию</h4>
        </div>
        <PhotoPuzzle v-if="place.photoUrl" :key="place.id" :photo-url="place.photoUrl" />
        <InlineNotice v-else icon="photo">
          Для этой точки пока нет фотографии в архиве — пазл появится, когда её добавят.
        </InlineNotice>
      </div>

      <!-- Взрослый режим — факты и видео о месте -->
      <template v-else>
        <div
          v-if="place.description"
          class="flex flex-col gap-space-xs rounded-2xl bg-surface-container-lowest p-space-md shadow-document"
        >
          <div class="flex items-center gap-space-xs text-on-surface-variant">
            <MsIcon name="menu_book" :size="18" class="text-primary" />
            <h4 class="font-archival text-archival uppercase">Об этом месте</h4>
          </div>
          <p class="font-body-md text-body-md text-on-surface-variant">{{ place.description }}</p>
        </div>
        <InlineNotice v-else icon="menu_book">Подробностей об этой точке пока не внесли.</InlineNotice>

        <div
          v-if="place.videoUrl"
          class="flex flex-col gap-space-sm overflow-hidden rounded-2xl bg-night p-space-sm text-white shadow-sheet"
        >
          <div class="flex items-center gap-space-xs px-space-xs pt-space-xs text-white/75">
            <MsIcon name="slow_motion_video" :size="18" />
            <h4 class="font-archival text-archival uppercase">Видео</h4>
          </div>
          <video :src="place.videoUrl" controls playsinline class="w-full rounded-xl" />
        </div>
        <InlineNotice v-else icon="slow_motion_video">Видео для этой точки пока нет.</InlineNotice>
      </template>
    </template>
  </div>
</template>
