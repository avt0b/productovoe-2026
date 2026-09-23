<script setup lang="ts">
import { Browser } from '@capacitor/browser'
import { Capacitor } from '@capacitor/core'
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'

import { errorText } from '@/core/format'
import {
  distanceKm,
  formatDistance,
  formatWalkDuration,
  geolocationProblem,
  walkingDirectionsUrl,
  type GeoMarker,
  type GeoPath,
} from '@/core/geo'
import GeoMap from '@/ui/geo/GeoMap.vue'
import MsIcon from '@/ui/MsIcon.vue'

import DestinationPicker from './components/DestinationPicker.vue'
import { finishWalk, leadWalk, type WalkTarget } from './data'
import { useWalk } from './useWalk'

/**
 * Карта идущей группы.
 *
 * У всех одна картина: где краевед (своя метка), где остальные, куда идём и
 * как туда дойти от себя. Краевед здесь же меняет цель и заканчивает
 * экскурсию — отдельного пульта у него нет, он идёт вместе с группой.
 */
const props = defineProps<{ excursionId: string }>()

const router = useRouter()
const { walk, loadError, route, position, geoStatus, metersLeft, arrived, refresh, rerouteNow } = useWalk(
  props.excursionId,
)

const isGuide = computed(() => walk.value?.is_guide ?? false)
const destination = computed(() => walk.value?.destination ?? null)
const others = computed(() => (walk.value?.members ?? []).filter((member) => !member.is_me))
const guide = computed(() => others.value.find((member) => member.is_guide) ?? null)

const markers = computed<GeoMarker[]>(() => {
  const list: GeoMarker[] = others.value.map((member) =>
    member.is_guide
      ? { id: member.user_id, lat: member.lat, lon: member.lon, label: 'Краевед', icon: 'hiking', tone: 'tertiary' }
      : { id: member.user_id, lat: member.lat, lon: member.lon, label: 'Участник', icon: 'person', tone: 'secondary' },
  )
  const target = destination.value
  if (target) {
    list.push({
      id: 'destination',
      lat: target.lat,
      lon: target.lon,
      label: target.name || 'Памятное место',
      icon: 'flag',
      tone: 'primary',
    })
  }
  return list
})

const paths = computed<GeoPath[]>(() =>
  route.value && !arrived.value
    ? [{ id: 'route', points: route.value.points, tone: 'primary', dashed: route.value.estimated }]
    : [],
)

/** Главная строка панели: сколько идти или что мешает это посчитать. */
const summary = computed(() => {
  if (arrived.value) return 'Вы на месте'
  const problem = geolocationProblem(geoStatus.value)
  if (problem) return problem
  if (!position.value) return 'Определяю, где вы…'
  if (route.value) {
    const how = route.value.estimated ? 'по прямой' : 'пешком'
    return `${formatDistance(route.value.distanceMeters / 1000)} · ${formatWalkDuration(route.value.durationSeconds)} ${how}`
  }
  return metersLeft.value !== null ? formatDistance(metersLeft.value / 1000) : 'Строю маршрут…'
})

/** Где краевед относительно участника — чтобы не отстать от группы. */
const guideHint = computed(() => {
  if (isGuide.value) {
    const count = others.value.length
    return count === 0 ? 'Группа ещё не прислала точки' : `На карте ${count} из группы`
  }
  const me = position.value
  if (!guide.value) return 'Краевед пока не на связи'
  if (!me) return 'Краевед на карте'
  return `Краевед в ${formatDistance(distanceKm(me, guide.value))} от вас`
})

// --- действия ---

const picking = ref(false)
const busy = ref(false)
const actionError = ref<string | null>(null)
const confirmFinish = ref(false)

async function changeDestination(target: WalkTarget): Promise<void> {
  if (busy.value) return
  busy.value = true
  actionError.value = null
  try {
    walk.value = await leadWalk(props.excursionId, target)
    picking.value = false
    void rerouteNow()
  } catch (reason) {
    actionError.value = errorText(reason)
  } finally {
    busy.value = false
  }
}

async function finish(): Promise<void> {
  if (!confirmFinish.value) {
    confirmFinish.value = true
    return
  }
  busy.value = true
  actionError.value = null
  try {
    walk.value = await finishWalk(props.excursionId)
  } catch (reason) {
    actionError.value = errorText(reason)
  } finally {
    busy.value = false
    confirmFinish.value = false
  }
}

/** Пешеходный маршрут во внешних Картах: голосом и с поворотами они ведут лучше нас. */
async function openNavigator(): Promise<void> {
  const target = destination.value
  if (!target) return
  const url = walkingDirectionsUrl(position.value, target)
  if (Capacitor.isNativePlatform()) await Browser.open({ url })
  else window.open(url, '_blank', 'noopener')
}

function back(): void {
  void router.push({ name: 'excursion', params: { excursionId: props.excursionId } })
}

const pickFrom = computed(() => position.value ?? destination.value ?? { lat: 52.9686, lon: 36.0694 })
</script>

<template>
  <div class="fixed inset-0 z-0 flex flex-col bg-surface">
    <GeoMap
      class="absolute inset-0"
      :markers="markers"
      :paths="paths"
      :user="position"
      :locating="geoStatus === 'locating'"
      follow
    />

    <!-- Верх: назад и что за экран. -->
    <div class="pointer-events-none relative z-10 flex items-center gap-space-sm px-space-sm pt-safe">
      <button
        type="button"
        aria-label="К экскурсии"
        class="pointer-events-auto mt-space-sm flex h-11 w-11 items-center justify-center rounded-full bg-surface-container-lowest text-on-surface shadow-lg active:scale-95"
        @click="back"
      >
        <MsIcon name="arrow_back" :size="22" />
      </button>
      <div
        class="pointer-events-auto mt-space-sm flex min-w-0 items-center gap-space-xs rounded-full bg-surface-container-lowest px-space-md py-2 shadow-lg"
      >
        <span class="h-2 w-2 shrink-0 animate-pulse rounded-full bg-primary" />
        <span class="truncate font-label-lg text-label-lg text-on-surface">
          {{ walk?.status === 'walking' ? 'Группа идёт' : 'Карта группы' }}
        </span>
      </div>
    </div>

    <!-- Низ: куда идём, сколько, и действия. -->
    <div class="pointer-events-none absolute inset-x-0 bottom-0 z-10 px-space-sm pb-safe">
      <div class="pointer-events-auto mb-space-sm flex flex-col gap-space-sm rounded-xl bg-surface-container-lowest p-space-md shadow-xl">
        <template v-if="loadError">
          <p class="font-body-md text-body-md text-error">{{ loadError }}</p>
          <button type="button" class="self-start font-label-lg text-label-lg text-primary" @click="refresh">
            Повторить
          </button>
        </template>

        <p v-else-if="!walk" class="font-body-md text-body-md text-on-surface-variant">Загружаю карту группы…</p>

        <template v-else-if="walk.status === 'finished'">
          <div class="flex items-center gap-space-sm">
            <span class="flex h-10 w-10 items-center justify-center rounded-full bg-primary-container text-on-primary-container">
              <MsIcon name="celebration" :size="22" />
            </span>
            <div class="flex flex-col">
              <p class="font-headline-sm text-headline-sm text-on-surface">Экскурсия завершена</p>
              <p class="font-body-sm text-body-sm text-on-surface-variant">Спасибо, что были с группой</p>
            </div>
          </div>
          <button
            type="button"
            class="h-11 rounded-full bg-primary font-label-lg text-label-lg text-on-primary active:scale-[0.98]"
            @click="back"
          >
            К экскурсии
          </button>
        </template>

        <template v-else-if="walk.status !== 'walking' || !destination">
          <p class="font-body-md text-body-md text-on-surface-variant">
            Группа ещё не вышла — карта откроется сама, как только краевед поведёт всех к месту.
          </p>
        </template>

        <template v-else>
          <div class="flex items-start gap-space-sm">
            <span
              class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full"
              :class="arrived ? 'bg-primary text-on-primary' : 'bg-primary-container text-on-primary-container'"
            >
              <MsIcon :name="arrived ? 'where_to_vote' : 'flag'" :size="22" />
            </span>
            <div class="flex min-w-0 flex-1 flex-col">
              <p class="truncate font-headline-sm text-headline-sm text-on-surface">
                {{ destination.name || 'Памятное место' }}
              </p>
              <p class="font-label-lg text-label-lg" :class="arrived ? 'text-primary' : 'text-on-surface'">
                {{ summary }}
              </p>
              <p class="font-body-sm text-body-sm text-on-surface-variant">{{ guideHint }}</p>
            </div>
          </div>

          <p v-if="actionError" class="font-body-sm text-body-sm text-error">{{ actionError }}</p>

          <div class="flex gap-space-xs">
            <button
              type="button"
              class="flex h-11 flex-1 items-center justify-center gap-space-xs rounded-full bg-primary font-label-lg text-label-lg text-on-primary active:scale-[0.98]"
              @click="openNavigator"
            >
              <MsIcon name="navigation" :size="18" />
              Навигатор
            </button>
            <button
              v-if="isGuide"
              type="button"
              class="flex h-11 flex-1 items-center justify-center gap-space-xs rounded-full bg-secondary-container font-label-lg text-label-lg text-on-secondary-container active:scale-[0.98] disabled:opacity-60"
              :disabled="busy"
              @click="picking = true"
            >
              <MsIcon name="alt_route" :size="18" />
              Дальше
            </button>
          </div>

          <button
            v-if="isGuide"
            type="button"
            class="h-10 rounded-full font-label-lg text-label-lg active:scale-[0.98] disabled:opacity-60"
            :class="confirmFinish ? 'bg-error text-on-error' : 'text-on-surface-variant'"
            :disabled="busy"
            @click="finish"
          >
            {{ confirmFinish ? 'Точно завершить? Нажмите ещё раз' : 'Завершить экскурсию' }}
          </button>
        </template>
      </div>
    </div>

    <DestinationPicker
      v-if="picking"
      :from="pickFrom"
      :current-poi-id="destination?.poi_id"
      :busy="busy"
      @close="picking = false"
      @pick="changeDestination"
    />
  </div>
</template>
