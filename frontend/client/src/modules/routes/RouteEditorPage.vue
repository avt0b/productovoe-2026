<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { useAsync } from '@/core/async'
import { errorText } from '@/core/format'
import { OREL_CENTER, type GeoMarker, type GeoPath, type LatLon } from '@/core/geo'
import {
  deleteRoute,
  deleteWaypoint,
  getMyRoute,
  publishRoute,
  reorderWaypoints,
  type RouteDetail,
  type Waypoint,
} from '@/core/services/routes'
import InlineNotice from '@/ui/InlineNotice.vue'
import MsIcon from '@/ui/MsIcon.vue'
import StateBlock from '@/ui/StateBlock.vue'
import GeoMap from '@/ui/geo/GeoMap.vue'

import RouteFormSheet from './components/RouteFormSheet.vue'
import WaypointSheet from './components/WaypointSheet.vue'

/**
 * Редактор маршрута краеведа: точки, их порядок и публикация.
 *
 * Порядок точек — это и есть маршрут: сервис отдаёт их по `order_index`, семья
 * идёт по нему же. Поэтому «выше/ниже» меняет индексы на сервере, а не только
 * на экране.
 */
const route = useRoute()
const router = useRouter()

const routeId = computed(() => String(route.params.routeId ?? ''))
const { data, loading, error, retry } = useAsync<RouteDetail>(() => getMyRoute(routeId.value))

const editing = ref(false)
const waypointOpen = ref(false)
const editedWaypoint = ref<Waypoint | null>(null)
const confirmingDelete = ref(false)
const busy = ref(false)
const actionError = ref<string | null>(null)
const notice = ref<string | null>(null)

const waypoints = computed(() => [...(data.value?.waypoints ?? [])].sort((a, b) => a.order_index - b.order_index))

/** Куда ставить новую точку по умолчанию: рядом с последней, иначе центр Орла. */
const nextPoint = computed<LatLon>(() => {
  const last = waypoints.value[waypoints.value.length - 1]
  return last ? { lat: last.lat, lon: last.lon } : OREL_CENTER
})

const markers = computed<GeoMarker[]>(() =>
  waypoints.value.map((point, index) => ({
    id: point.id,
    lat: point.lat,
    lon: point.lon,
    label: point.title,
    icon: 'flag',
    tone: 'primary',
    badge: String(index + 1),
  })),
)

const paths = computed<GeoPath[]>(() =>
  waypoints.value.length > 1
    ? [{ id: 'route', points: waypoints.value.map((point) => ({ lat: point.lat, lon: point.lon })), tone: 'primary', dashed: true }]
    : [],
)

/** Сервис не публикует маршрут без точек — говорим об этом заранее, а не ответом 409. */
const publishBlocked = computed(() => (waypoints.value.length ? null : 'Добавьте хотя бы одну точку — без них маршрут не опубликовать'))

async function act(work: () => Promise<unknown>, done?: string): Promise<void> {
  if (busy.value) return
  busy.value = true
  actionError.value = null
  notice.value = null
  try {
    await work()
    await retry()
    if (done) notice.value = done
  } catch (reason) {
    actionError.value = errorText(reason)
  } finally {
    busy.value = false
  }
}

function togglePublish(): void {
  const current = data.value
  if (!current || (publishBlocked.value && !current.is_published)) return
  void act(
    () => publishRoute(current.id, !current.is_published),
    current.is_published ? 'Маршрут снят с публикации — семьи его больше не видят' : 'Маршрут опубликован — он появился у семей',
  )
}

/**
 * Поменять точку местами с соседней. Порядок уезжает на сервер целиком
 * (`/waypoints/reorder`): он сам расставит индексы, и на полпути не остаётся
 * двух точек с одним номером.
 */
function move(index: number, delta: number): void {
  const list = waypoints.value
  if (!list[index] || !list[index + delta]) return
  const order = list.map((point) => point.id)
  ;[order[index], order[index + delta]] = [order[index + delta], order[index]]
  void act(() => reorderWaypoints(routeId.value, order))
}

function openWaypoint(point: Waypoint | null): void {
  editedWaypoint.value = point
  waypointOpen.value = true
}

function removeWaypoint(point: Waypoint): void {
  void act(() => deleteWaypoint(point.id), 'Точка удалена')
}

async function removeRoute(): Promise<void> {
  if (!data.value || busy.value) return
  busy.value = true
  actionError.value = null
  try {
    await deleteRoute(data.value.id)
    await router.replace({ name: 'my-routes' })
  } catch (reason) {
    actionError.value = errorText(reason)
    busy.value = false
  }
}
</script>

<template>
  <div class="flex w-full flex-col gap-space-md px-margin short:gap-space-sm">
    <StateBlock v-if="loading || error" :loading="loading" :error="error" @retry="retry" />

    <template v-else-if="data">
      <section class="flex flex-col gap-space-sm rounded-2xl bg-surface-container-lowest p-space-md shadow-document">
        <div class="flex items-start justify-between gap-space-sm">
          <div class="min-w-0">
            <p class="font-archival text-archival uppercase text-on-surface-variant">
              {{ data.is_published ? 'Опубликован' : 'Черновик' }}{{ data.mode === 'family' ? ' · семейный' : '' }}
            </p>
            <h1 class="break-words font-headline-md text-headline-md text-on-surface">{{ data.title }}</h1>
            <p v-if="data.city || data.distance_km" class="font-body-sm text-body-sm text-on-surface-variant">
              {{ [data.city, data.distance_km ? `${data.distance_km} км` : ''].filter(Boolean).join(' · ') }}
            </p>
          </div>
          <button
            type="button"
            aria-label="Изменить маршрут"
            class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-surface-container-high text-on-surface active:scale-95"
            @click="editing = true"
          >
            <MsIcon name="edit" :size="18" />
          </button>
        </div>
        <p v-if="data.description" class="whitespace-pre-line font-body-md text-body-md text-on-surface">{{ data.description }}</p>
      </section>

      <GeoMap
        v-if="markers.length"
        :markers="markers"
        :paths="paths"
        :center="nextPoint"
        label="Точки маршрута по порядку"
        class="h-56 w-full rounded-2xl shadow-document short:h-44"
      />

      <section class="flex flex-col gap-space-sm">
        <div class="flex items-end justify-between gap-space-sm">
          <h2 class="font-headline-md text-headline-md text-on-surface">Точки маршрута</h2>
          <button
            type="button"
            class="flex items-center gap-space-xs rounded-full bg-surface-container-high px-space-md py-2 font-label-md text-label-md text-on-surface active:scale-95"
            @click="openWaypoint(null)"
          >
            <MsIcon name="add" :size="18" />
            Добавить
          </button>
        </div>

        <StateBlock
          v-if="!waypoints.length"
          :loading="false"
          :error="null"
          empty
          empty-icon="flag"
          empty-text="Точек пока нет. Добавьте первую — с рассказом и заданием для ребёнка"
        />

        <article
          v-for="(point, index) in waypoints"
          :key="point.id"
          class="flex flex-col gap-space-sm rounded-2xl bg-surface-container-lowest p-space-md shadow-document"
        >
          <div class="flex items-start gap-space-sm">
            <span
              class="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary-container font-label-md text-label-md text-white"
              aria-hidden="true"
            >
              {{ index + 1 }}
            </span>
            <div class="min-w-0 flex-1">
              <p class="font-headline-sm text-headline-sm text-on-surface">{{ point.title }}</p>
              <p v-if="point.story" class="line-clamp-2 font-body-sm text-body-sm text-on-surface-variant">{{ point.story }}</p>
            </div>
          </div>

          <ul class="flex flex-wrap gap-space-xs">
            <li
              v-if="point.kid_task"
              class="flex items-center gap-1 rounded-full bg-surface-container-high px-2 py-0.5 font-label-sm text-label-sm text-on-surface"
            >
              <MsIcon name="extension" :size="15" />
              задание
            </li>
            <li
              v-if="point.has_answer"
              class="flex items-center gap-1 rounded-full bg-secondary-container px-2 py-0.5 font-label-sm text-label-sm text-on-secondary-container"
            >
              <MsIcon name="task_alt" :size="15" />
              с ответом
            </li>
            <li
              v-if="point.ar_hint"
              class="flex items-center gap-1 rounded-full bg-tertiary-fixed px-2 py-0.5 font-label-sm text-label-sm text-on-tertiary-fixed"
            >
              <MsIcon name="view_in_ar" :size="15" />
              AR
            </li>
          </ul>

          <div class="flex items-center justify-between gap-space-xs border-t border-outline-variant/60 pt-space-sm">
            <div class="flex items-center gap-space-xs">
              <button
                type="button"
                aria-label="Выше по маршруту"
                class="flex h-9 w-9 items-center justify-center rounded-full bg-surface-container-high text-on-surface active:scale-95 disabled:opacity-40"
                :disabled="index === 0 || busy"
                @click="move(index, -1)"
              >
                <MsIcon name="arrow_upward" :size="18" />
              </button>
              <button
                type="button"
                aria-label="Ниже по маршруту"
                class="flex h-9 w-9 items-center justify-center rounded-full bg-surface-container-high text-on-surface active:scale-95 disabled:opacity-40"
                :disabled="index === waypoints.length - 1 || busy"
                @click="move(index, 1)"
              >
                <MsIcon name="arrow_downward" :size="18" />
              </button>
            </div>
            <div class="flex items-center gap-space-xs">
              <button
                type="button"
                class="rounded-full px-space-sm py-2 font-label-md text-label-md text-error active:scale-95 disabled:opacity-60"
                :disabled="busy"
                @click="removeWaypoint(point)"
              >
                Удалить
              </button>
              <button
                type="button"
                class="flex items-center gap-space-xs rounded-full bg-surface-container-high px-space-md py-2 font-label-md text-label-md text-on-surface active:scale-95"
                @click="openWaypoint(point)"
              >
                <MsIcon name="edit" :size="18" />
                Править
              </button>
            </div>
          </div>
        </article>
      </section>

      <InlineNotice v-if="actionError" tone="error">{{ actionError }}</InlineNotice>
      <InlineNotice v-else-if="notice" tone="success">{{ notice }}</InlineNotice>
      <InlineNotice v-else-if="publishBlocked && !data.is_published" tone="info">{{ publishBlocked }}</InlineNotice>

      <button
        type="button"
        class="flex w-full items-center justify-center space-x-space-sm rounded-xl py-3.5 font-label-lg text-label-lg uppercase tracking-wide shadow-stamp transition-all active:scale-[0.99] disabled:opacity-60 short:py-2.5"
        :class="data.is_published ? 'bg-surface-container-high text-on-surface' : 'bg-primary-container text-white hover:bg-primary'"
        :disabled="busy || (!data.is_published && publishBlocked !== null)"
        @click="togglePublish"
      >
        <MsIcon :name="busy ? 'progress_activity' : data.is_published ? 'visibility_off' : 'public'" :size="18" :class="{ 'animate-spin': busy }" />
        <span>{{ data.is_published ? 'Снять с публикации' : 'Опубликовать маршрут' }}</span>
      </button>

      <!-- Удаление — в два нажатия: случайный тап не должен стирать работу. -->
      <div class="flex flex-col">
        <button
          type="button"
          class="self-center rounded-full px-space-md py-2 font-label-md text-label-md text-error active:scale-95"
          :aria-expanded="confirmingDelete"
          @click="confirmingDelete = !confirmingDelete"
        >
          Удалить маршрут
        </button>
        <div
          class="grid transition-[grid-template-rows,opacity] duration-300 ease-out"
          :class="confirmingDelete ? 'grid-rows-[1fr] opacity-100' : 'grid-rows-[0fr] opacity-0'"
          :inert="!confirmingDelete"
        >
          <div class="overflow-hidden">
            <div
              class="mt-space-sm flex flex-col gap-space-sm rounded-2xl bg-surface-container-lowest p-space-md shadow-document"
              role="alertdialog"
              aria-label="Подтверждение удаления"
            >
              <p class="font-body-sm text-body-sm text-on-surface">
                Удалить маршрут вместе со всеми точками? Это не отменить.
              </p>
              <div class="flex gap-space-sm">
                <button
                  type="button"
                  class="flex-1 rounded-full bg-surface-container-high py-2.5 font-label-md text-label-md text-on-surface active:scale-95"
                  @click="confirmingDelete = false"
                >
                  Оставить
                </button>
                <button
                  type="button"
                  class="flex flex-1 items-center justify-center gap-1.5 rounded-full bg-error py-2.5 font-label-md text-label-md text-on-error active:scale-95 disabled:opacity-60"
                  :disabled="busy"
                  @click="removeRoute"
                >
                  <MsIcon name="delete" :size="18" />
                  Удалить
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <RouteFormSheet v-if="editing" :route="data" @close="editing = false" @saved="retry" />
      <WaypointSheet
        v-if="waypointOpen"
        :route-id="data.id"
        :waypoint="editedWaypoint"
        :near="nextPoint"
        @close="waypointOpen = false"
        @saved="retry"
      />
    </template>
  </div>
</template>
