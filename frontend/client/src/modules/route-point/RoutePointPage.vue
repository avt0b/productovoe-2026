<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'

import { useAsync } from '@/core/async'
import { shareCurrentPage } from '@/core/share'
import MsIcon from '@/ui/MsIcon.vue'
import StateBlock from '@/ui/StateBlock.vue'

import CompareSlider from './components/CompareSlider.vue'
import EpochAudioCard from './components/EpochAudioCard.vue'
import FamilyQuestCard from './components/FamilyQuestCard.vue'
import { fetchRoutePoint } from './data'

const props = defineProps<{ pointId: string }>()

const router = useRouter()
const { data: point, loading, error, retry } = useAsync(() => fetchRoutePoint(props.pointId))

const bookmarked = ref(false)
const arNotice = ref(false)

const canOpenMap = computed(() => router.hasRoute('routes'))

function openWalkingRoute(): void {
  if (canOpenMap.value) void router.push({ name: 'routes' })
}
</script>

<template>
  <div class="flex w-full flex-col gap-space-md px-margin pb-space-xl">
    <StateBlock v-if="loading || error" :loading="loading" :error="error" class="mt-space-md" @retry="retry" />

    <template v-else-if="point">
      <!-- Где мы на маршруте -->
      <div class="flex items-center justify-between pt-space-xs">
        <div
          class="inline-flex items-center gap-space-xs rounded-full bg-secondary-container px-3 py-1 font-label-md text-label-md text-on-secondary-fixed-variant"
        >
          <MsIcon name="flag" :size="16" />
          <span>Точка {{ point.step }} из {{ point.totalSteps }} • {{ point.routeTitle }}</span>
        </div>
        <div class="flex items-center gap-space-xs">
          <button
            type="button"
            :aria-label="bookmarked ? 'Убрать из закладок' : 'Добавить в закладки'"
            :aria-pressed="bookmarked"
            class="flex h-9 w-9 items-center justify-center rounded-full bg-surface-container-low transition-transform hover:bg-surface-container active:scale-95"
            :class="bookmarked ? 'text-primary' : 'text-on-surface'"
            @click="bookmarked = !bookmarked"
          >
            <MsIcon :name="bookmarked ? 'bookmark' : 'bookmark_border'" :size="20" :filled="bookmarked" />
          </button>
          <button
            type="button"
            aria-label="Поделиться точкой"
            class="flex h-9 w-9 items-center justify-center rounded-full bg-surface-container-low text-on-surface transition-transform hover:bg-surface-container active:scale-95"
            @click="shareCurrentPage(point.title)"
          >
            <MsIcon name="share" :size="20" />
          </button>
        </div>
      </div>

      <!-- Название -->
      <div class="flex flex-col gap-space-xs">
        <h2 class="font-headline-lg-mobile text-headline-lg-mobile text-on-surface">{{ point.title }}</h2>
        <p class="flex items-center gap-1.5 font-body-md text-body-md text-on-surface-variant">
          <MsIcon name="explore" :size="18" class="text-secondary" />
          <span>{{ point.place }}</span>
        </p>
        <div
          class="mt-space-xs inline-flex items-center gap-1.5 self-start rounded-full bg-secondary-container/70 px-3 py-1 font-label-md text-label-md text-on-secondary-fixed-variant"
        >
          <MsIcon name="verified" :size="16" filled class="text-secondary" />
          <span>{{ point.verifiedBy }}</span>
        </div>
      </div>

      <CompareSlider v-bind="point.comparison" />

      <EpochAudioCard v-bind="point.audio" />

      <FamilyQuestCard v-bind="point.quest" />

      <!-- Воспоминания -->
      <div class="flex flex-col gap-space-xs rounded-DEFAULT bg-surface-container-lowest p-space-md shadow-sm">
        <div class="flex items-center gap-space-xs text-on-surface">
          <MsIcon name="menu_book" :size="20" class="text-primary" />
          <h4 class="font-label-lg text-label-lg">Из воспоминаний очевидца</h4>
        </div>
        <p class="font-body-sm text-body-sm italic text-on-surface-variant">{{ point.witness }}</p>
      </div>

      <!-- Действия -->
      <div class="flex flex-col gap-space-xs pt-space-xs">
        <button
          type="button"
          class="flex w-full items-center justify-center gap-2 rounded-full bg-primary py-3.5 font-label-lg text-label-lg text-on-primary shadow-md transition-all hover:bg-primary-container active:scale-[0.99] disabled:opacity-60"
          :disabled="!canOpenMap"
          @click="openWalkingRoute"
        >
          <MsIcon name="directions_walk" :size="20" />
          <span>Построить пеший маршрут ({{ point.walkingDistanceMeters }} м)</span>
        </button>
        <button
          type="button"
          class="flex w-full items-center justify-center gap-2 rounded-full bg-surface-container-lowest py-3 font-label-lg text-label-lg text-secondary shadow-sm transition-all hover:bg-surface-container-low active:scale-[0.99]"
          @click="arNotice = true"
        >
          <MsIcon name="view_in_ar" :size="20" />
          <span>Запустить AR-поиск {{ point.arTarget }}</span>
        </button>
        <p
          v-if="arNotice"
          class="flex items-start gap-2 rounded-DEFAULT bg-tertiary-fixed/40 px-3 py-2 font-body-sm text-body-sm text-on-tertiary-fixed-variant"
          role="status"
        >
          <MsIcon name="smartphone" :size="18" class="mt-0.5 shrink-0" />
          AR-поиск работает в мобильном приложении: камера и компас телефона наведут на место прямо на местности.
        </p>
      </div>
    </template>
  </div>
</template>
