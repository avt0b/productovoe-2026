<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { useAsync } from '@/core/async'
import { errorText } from '@/core/format'
import { formatDistance } from '@/core/geo'
import { completeWaypoint, getMyProgress, type RouteProgress } from '@/core/services/routes'
import { useSessionStore } from '@/core/session'
import { shareCurrentPage } from '@/core/share'
import { ArHintCard, buildSubtitles, isArAvailable, openAr } from '@/features/ar'
import DemoDataBadge from '@/ui/DemoDataBadge.vue'
import InlineNotice from '@/ui/InlineNotice.vue'
import MsIcon from '@/ui/MsIcon.vue'
import StateBlock from '@/ui/StateBlock.vue'

import { useBookmarks } from './bookmarks'
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

/** Закладка живёт в браузере: своей ручки у сервиса нет, но выбор должен переживать перезагрузку. */
const bookmarks = useBookmarks()
const bookmarked = computed(() => bookmarks.has(props.pointId))
/** Что ответил AR-экран в прошлый раз. `null` — ещё не запускали. */
const arNote = ref<string | null>(null)
const arBusy = ref(false)

/** AR живёт в APK вместе с нативным модулем; в браузере его нет. */
const arReady = isArAvailable()

/** Табличка точки: печатается из `mobile/tools/make_marker.py`. Пока одна, демонстрационная. */
const AR_MARKER = 'markers/wp-2.png'

const AR_PROBLEMS: Record<string, string> = {
  CAMERA_PERMISSION_DENIED: 'Без доступа к камере AR не работает — разрешите камеру в настройках телефона.',
  NO_CAMERA: 'На этом устройстве нет камеры — пройдите точку по карточке.',
  NO_ORIENTATION_SENSOR: 'На этом устройстве нет компаса — AR наводить не на что.',
}

// «Дальше» открывает тот же экран с другой точкой: компонент переиспользуется, данные надо перезагрузить.
watch([() => props.pointId, routeId], () => {
  arNote.value = null
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

/**
 * AR-поиск: нативный экран из `mobile/ar` наводит на точку по компасу, а у
 * печатной таблички ставит проводника прямо на неё. Нашли — точка засчитана.
 */
async function launchAr(): Promise<void> {
  const current = point.value
  if (!current || arBusy.value) return
  if (!arReady) {
    arNote.value = 'AR-поиск работает в мобильном приложении: нужны камера и компас телефона.'
    return
  }

  arBusy.value = true
  arNote.value = null
  try {
    const result = await openAr({
      pointId: current.id,
      title: current.title,
      stepIndex: current.step,
      stepTotal: current.totalSteps,
      target: { ...current.location, label: current.arHint ?? current.title },
      // У братской могилы и мемориала маскот сам не выходит, но наш QR-код
      // вызывает его всегда. Модель — орлёнок из mobile/ar (companion/chick.glb).
      companion: {
        name: 'Проводник маршрута',
        subtitle: current.routeTitle,
        asset: 'companion/chick.glb',
        onlyOnQr: current.solemn,
      },
      narration: {
        audioUrl: current.audioUrl,
        subtitles: buildSubtitles(current.story ?? current.title),
        // Строки нарезаны из текста, а не размечены по голосу: с озвучкой
        // модуль подгонит их сам, иначе она уйдёт вперёд субтитров.
        subtitlesAreEstimated: true,
      },
      marker: { asset: AR_MARKER, fallbackAfterMs: 4000 },
    })
    if (result.outcome === 'completed') {
      arNote.value = 'Метку нашли — точка засчитана.'
      await markDone()
    } else if (result.outcome === 'unavailable') {
      arNote.value = AR_PROBLEMS[result.reason ?? ''] ?? 'AR на этом устройстве недоступен — пройдите точку по карточке.'
    }
  } catch (reason) {
    arNote.value = errorText(reason)
  } finally {
    arBusy.value = false
  }
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
            @click="bookmarks.toggle(props.pointId)"
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
      <div v-if="canTrack" class="flex flex-col gap-1.5 rounded-2xl bg-surface-container-lowest p-space-sm shadow-document">
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
        <h2
          class="ribbon-shimmer font-headline-lg-mobile text-headline-lg-mobile text-on-surface [--shimmer-base:theme(colors.ink.DEFAULT)]"
        >
          {{ point.title }}
        </h2>
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
      <div v-if="point.story" class="flex flex-col gap-space-xs rounded-2xl bg-surface-container-lowest p-space-md shadow-document">
        <div class="flex items-center gap-space-xs text-on-surface-variant">
          <MsIcon name="menu_book" :size="18" class="text-primary" />
          <h4 class="font-archival text-archival uppercase">История места</h4>
        </div>
        <p class="font-body-md text-body-md text-on-surface-variant">{{ point.story }}</p>
      </div>

      <CompareSlider v-if="point.comparison" v-bind="point.comparison" />

      <EpochAudioCard
        v-if="point.audioUrl"
        :key="point.id"
        :src="point.audioUrl"
        :title="point.title"
        :author="point.routeTitle"
      />

      <FamilyQuestCard v-if="point.quest" :key="point.id" v-bind="point.quest" @done="markDone" />

      <!-- Действия -->
      <div class="flex flex-col gap-space-xs pt-space-xs">
        <button
          v-if="canTrack && !isDone"
          type="button"
          class="flex w-full items-center justify-center gap-space-sm rounded-xl bg-secondary px-space-md py-3.5 font-label-lg text-label-lg text-on-secondary shadow-float transition-all active:scale-[0.99] disabled:opacity-60"
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
          class="flex w-full items-center justify-center gap-space-sm rounded-xl bg-primary-container px-space-md py-3.5 font-label-lg text-label-lg uppercase tracking-wide text-white shadow-stamp transition-all hover:bg-primary active:scale-[0.99]"
          @click="openNext"
        >
          <MsIcon name="directions_walk" :size="20" class="shrink-0" />
          <span class="truncate">Дальше: {{ point.next.title }}</span>
          <span class="shrink-0 opacity-80">· {{ formatDistance(point.next.distanceKm) }}</span>
        </button>
        <InlineNotice v-else-if="routeFinished" tone="success" icon="emoji_events">
          Маршрут пройден — спасибо, что помните!
        </InlineNotice>
        <InlineNotice v-else-if="!canTrack" icon="flag">Последняя точка маршрута.</InlineNotice>
        <InlineNotice v-else icon="flag">Последняя точка — отметьте все точки, чтобы маршрут засчитался.</InlineNotice>

        <div class="grid gap-space-xs" :class="canOpenMap && point.arHint ? 'grid-cols-2' : 'grid-cols-1'">
          <button
            v-if="canOpenMap"
            type="button"
            class="flex items-center justify-center gap-1.5 rounded-2xl bg-surface-container-lowest px-space-sm py-3 font-label-md text-label-md text-on-surface shadow-document transition-colors hover:bg-surface-container-low active:scale-[0.99]"
            @click="openMap"
          >
            <MsIcon name="map" :size="20" class="shrink-0" />
            <span class="truncate">Маршрут на карте</span>
          </button>

          <button
            v-if="point.arHint"
            type="button"
            class="flex items-center justify-center gap-1.5 rounded-2xl bg-surface-container-lowest px-space-sm py-3 font-label-md text-label-md text-secondary shadow-document transition-colors hover:bg-surface-container-low active:scale-[0.99] disabled:opacity-60"
            :disabled="arBusy"
            @click="launchAr"
          >
            <MsIcon :name="arBusy ? 'progress_activity' : 'view_in_ar'" :size="20" :class="{ 'animate-spin': arBusy }" />
            <span class="truncate">AR-поиск</span>
          </button>
        </div>
        <ArHintCard v-if="point.arHint" :hint="point.arHint" :note="arNote" />
      </div>
    </template>
  </div>
</template>
