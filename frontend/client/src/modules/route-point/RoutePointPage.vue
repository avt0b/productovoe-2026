<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { useAsync } from '@/core/async'
import { errorText } from '@/core/format'
import { formatDistance } from '@/core/geo'
import { completeWaypoint, getMyProgress, type RouteProgress } from '@/core/services/routes'
import { useSessionStore } from '@/core/session'
import { shareCurrentPage } from '@/core/share'
import DemoDataBadge from '@/ui/DemoDataBadge.vue'
import InlineNotice from '@/ui/InlineNotice.vue'
import MsIcon from '@/ui/MsIcon.vue'
import StateBlock from '@/ui/StateBlock.vue'

import CompareSlider from './components/CompareSlider.vue'
import EpochAudioCard from './components/EpochAudioCard.vue'
import FamilyQuestCard from './components/FamilyQuestCard.vue'
import { fetchRoutePoint } from './data'

const props = defineProps<{ pointId: string }>()

const currentRoute = useRoute()
const router = useRouter()
const session = useSessionStore()

/** Маршрут, в котором открыта точка, — из `?route=`. */
const routeId = computed(() => (typeof currentRoute.query.route === 'string' ? currentRoute.query.route : null))

const { data: point, loading, error, retry } = useAsync(() => fetchRoutePoint(props.pointId, routeId.value))

const bookmarked = ref(false)
const arNotice = ref(false)

// «Дальше» открывает тот же экран с другой точкой: компонент переиспользуется, данные надо перезагрузить.
watch([() => props.pointId, routeId], () => {
  arNotice.value = false
  progressError.value = null
  void retry()
})

/**
 * Прогресс маршрута хранит `route_service` — нужен аккаунт и живые данные:
 * у демо-маршрута на сервере нет таких точек.
 */
const progress = ref<RouteProgress | null>(null)
const savingProgress = ref(false)
const progressError = ref<string | null>(null)

const canTrack = computed(() => session.hasAccount && point.value?.source === 'live' && routeId.value !== null)
const isDone = computed(() => progress.value?.completed_waypoint_ids.includes(props.pointId) ?? false)
const doneCount = computed(() => progress.value?.completed_waypoint_ids.length ?? 0)
const routeFinished = computed(() => Boolean(progress.value?.completed_at))

watch(
  [point, canTrack],
  async () => {
    if (!canTrack.value || !routeId.value) {
      progress.value = null
      return
    }
    try {
      progress.value = await getMyProgress(routeId.value)
    } catch {
      // Прогресс — дополнение к точке: не загрузился — точка всё равно открыта.
      progress.value = null
    }
  },
  { immediate: true },
)

/** Засчитать точку: кнопкой, выполненным заданием или найденной AR-меткой. */
async function markDone(): Promise<void> {
  if (!canTrack.value || !routeId.value || isDone.value || savingProgress.value) return
  savingProgress.value = true
  progressError.value = null
  try {
    progress.value = await completeWaypoint(routeId.value, props.pointId)
  } catch (reason) {
    progressError.value = errorText(reason)
  } finally {
    savingProgress.value = false
  }
}

const canOpenMap = computed(() => router.hasRoute('routes'))

function openNext(): void {
  const next = point.value?.next
  if (!next || !routeId.value) return
  void router.push({ name: 'route-point', params: { pointId: next.id }, query: { route: routeId.value } })
}

function openMap(): void {
  if (canOpenMap.value) void router.push({ name: 'routes' })
}
</script>

<template>
  <div class="flex w-full flex-col gap-space-md px-margin pb-space-xl">
    <StateBlock v-if="loading || error" :loading="loading" :error="error" class="mt-space-md" @retry="retry" />

    <template v-else-if="point">
      <!-- Где мы на маршруте -->
      <div class="flex items-center justify-between gap-space-xs pt-space-xs">
        <div
          class="inline-flex min-w-0 items-center gap-space-xs rounded-full bg-secondary-container px-3 py-1 font-label-md text-label-md text-on-secondary-fixed-variant"
        >
          <MsIcon name="flag" :size="16" class="shrink-0" />
          <span class="truncate">Точка {{ point.step }} из {{ point.totalSteps }} • {{ point.routeTitle }}</span>
        </div>
        <div class="flex shrink-0 items-center gap-space-xs">
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

      <DemoDataBadge v-if="point.source === 'demo'" />

      <!-- Прогресс маршрута: сколько точек семья уже прошла -->
      <div v-if="canTrack" class="flex flex-col gap-1.5 rounded-DEFAULT bg-surface-container-low p-space-sm">
        <div class="flex items-center justify-between font-label-md text-label-md text-on-surface">
          <span>Пройдено {{ doneCount }} из {{ point.totalSteps }}</span>
          <span v-if="isDone" class="inline-flex items-center gap-1 text-secondary">
            <MsIcon name="check_circle" :size="16" filled />
            Точка пройдена
          </span>
        </div>
        <div
          class="h-2 w-full overflow-hidden rounded-full bg-surface-container-high"
          role="progressbar"
          :aria-valuenow="doneCount"
          aria-valuemin="0"
          :aria-valuemax="point.totalSteps"
          :aria-label="`Пройдено ${doneCount} из ${point.totalSteps}`"
        >
          <div class="h-full rounded-full bg-secondary transition-all duration-500" :style="{ width: `${(doneCount / point.totalSteps) * 100}%` }" />
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
          v-if="point.verifiedBy"
          class="mt-space-xs inline-flex items-center gap-1.5 self-start rounded-full bg-secondary-container/70 px-3 py-1 font-label-md text-label-md text-on-secondary-fixed-variant"
        >
          <MsIcon name="verified" :size="16" filled class="text-secondary" />
          <span>{{ point.verifiedBy }}</span>
        </div>
      </div>

      <!-- История места -->
      <div v-if="point.story" class="flex flex-col gap-space-xs rounded-DEFAULT bg-surface-container-lowest p-space-md shadow-sm">
        <div class="flex items-center gap-space-xs text-on-surface">
          <MsIcon name="menu_book" :size="20" class="text-primary" />
          <h4 class="font-label-lg text-label-lg">История места</h4>
        </div>
        <p class="font-body-md text-body-md text-on-surface-variant">{{ point.story }}</p>
      </div>

      <CompareSlider v-if="point.comparison" v-bind="point.comparison" />

      <EpochAudioCard v-if="point.audio" v-bind="point.audio" />

      <FamilyQuestCard v-if="point.quest" :key="point.id" v-bind="point.quest" @done="markDone" />

      <!-- Действия -->
      <div class="flex flex-col gap-space-xs pt-space-xs">
        <button
          v-if="canTrack && !isDone"
          type="button"
          class="flex w-full items-center justify-center gap-2 rounded-full bg-secondary px-space-md py-3.5 font-label-lg text-label-lg text-on-secondary shadow-md transition-all active:scale-[0.99] disabled:opacity-60"
          :disabled="savingProgress"
          @click="markDone"
        >
          <MsIcon :name="savingProgress ? 'progress_activity' : 'task_alt'" :size="20" :class="{ 'animate-spin': savingProgress }" />
          Я здесь — отметить точку пройденной
        </button>
        <InlineNotice v-if="progressError" tone="error">{{ progressError }}</InlineNotice>
        <InlineNotice v-else-if="!session.hasAccount" icon="bookmark_add">
          Войдите в аккаунт, чтобы пройденные точки сохранялись и маршрут засчитывался.
        </InlineNotice>

        <button
          v-if="point.next"
          type="button"
          class="flex w-full items-center justify-center gap-2 rounded-full bg-primary px-space-md py-3.5 font-label-lg text-label-lg text-on-primary shadow-md transition-all hover:bg-primary-container active:scale-[0.99]"
          @click="openNext"
        >
          <MsIcon name="directions_walk" :size="20" class="shrink-0" />
          <span class="truncate">Дальше: {{ point.next.title }}</span>
          <span class="shrink-0 opacity-80">· {{ formatDistance(point.next.distanceKm) }}</span>
        </button>
        <p
          v-else-if="routeFinished || !canTrack"
          class="flex items-center justify-center gap-2 rounded-full bg-secondary-container px-space-md py-3 font-label-lg text-label-lg text-on-secondary-container"
          role="status"
        >
          <MsIcon name="emoji_events" :size="20" />
          {{ routeFinished ? 'Маршрут пройден — спасибо, что помните!' : 'Последняя точка маршрута' }}
        </p>
        <p
          v-else
          class="flex items-center justify-center gap-2 rounded-full bg-surface-container-low px-space-md py-3 font-label-lg text-label-lg text-on-surface-variant"
          role="status"
        >
          <MsIcon name="flag" :size="20" />
          Последняя точка — отметьте все точки, чтобы пройти маршрут
        </p>

        <button
          v-if="canOpenMap"
          type="button"
          class="flex w-full items-center justify-center gap-2 rounded-full bg-surface-container-lowest py-3 font-label-lg text-label-lg text-on-surface shadow-sm transition-all hover:bg-surface-container-low active:scale-[0.99]"
          @click="openMap"
        >
          <MsIcon name="map" :size="20" />
          <span>Маршрут на карте</span>
        </button>

        <button
          v-if="point.arHint"
          type="button"
          class="flex w-full items-center justify-center gap-2 rounded-full bg-surface-container-lowest py-3 font-label-lg text-label-lg text-secondary shadow-sm transition-all hover:bg-surface-container-low active:scale-[0.99]"
          @click="arNotice = true"
        >
          <MsIcon name="view_in_ar" :size="20" />
          <span>Запустить AR-поиск</span>
        </button>
        <div
          v-if="arNotice && point.arHint"
          class="flex items-start gap-2 rounded-DEFAULT bg-tertiary-fixed/40 px-3 py-2 font-body-sm text-body-sm text-on-tertiary-fixed-variant"
          role="status"
        >
          <MsIcon name="smartphone" :size="18" class="mt-0.5 shrink-0" />
          <p>
            {{ point.arHint }}
            <span class="block pt-1 opacity-80">AR-поиск работает в мобильном приложении с камерой и компасом телефона.</span>
          </p>
        </div>
      </div>
    </template>
  </div>
</template>
