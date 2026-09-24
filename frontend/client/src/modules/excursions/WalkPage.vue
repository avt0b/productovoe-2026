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
    <!--
      Карта — подложка под панелями, поэтому её растягивает обёртка, а не класс
      снаружи: у самой `GeoMap` есть `relative`, и в Tailwind он перебивает
      переданный `absolute` (порядок в таблице стилей, а не в атрибуте). Из-за
      этого карта оказывалась нулевой высоты, и экран показывал пустой лист.
    -->
    <div class="absolute inset-0">
      <GeoMap
        class="h-full w-full"
        :markers="markers"
        :paths="paths"
        :user="position"
        :locating="geoStatus === 'locating'"
        follow
      />
    </div>

    <!-- Верх: назад и что за экран. -->
    <div class="pointer-events-none relative z-10 flex items-center gap-space-sm px-space-sm pt-safe">
      <button
        type="button"
        aria-label="К экскурсии"
        class="pointer-events-auto mt-space-sm flex h-11 w-11 items-center justify-center rounded-full border border-white/15 bg-night/55 text-white shadow-sheet backdrop-blur-md transition-colors hover:bg-night/70 active:scale-95"
        @click="back"
      >
        <MsIcon name="arrow_back" :size="22" />
      </button>
      <div
        class="pointer-events-auto mt-space-sm flex min-w-0 items-center gap-space-xs rounded-full border border-white/15 bg-night/55 px-space-md py-2 shadow-sheet backdrop-blur-md"
      >
        <span class="h-2 w-2 shrink-0 animate-pulse rounded-full bg-primary-fixed-dim" />
        <span class="truncate font-label-lg text-label-lg text-white">
          {{ walk?.status === 'walking' ? 'Группа идёт' : 'Карта группы' }}
        </span>
      </div>
    </div>

    <!-- Низ: куда идём, сколько, и действия. -->
    <div class="pointer-events-none absolute inset-x-0 bottom-0 z-10 px-space-sm pb-safe">
      <!--
        Карточка лежит на карте, поэтому она стеклянная и тёмная — как форма на
        экране входа поверх фотографии. На светлой подложке карта под ней
        просвечивала бы и мешала читать.
      -->
      <div
        class="pointer-events-auto mb-space-sm flex flex-col gap-space-sm rounded-2xl border border-white/15 bg-night/55 p-space-md shadow-sheet backdrop-blur-md"
      >
        <template v-if="loadError">
          <p class="rounded-xl bg-error/90 px-space-sm py-2 font-body-sm text-body-sm text-white" role="alert">{{ loadError }}</p>
          <button type="button" class="self-start font-label-lg text-label-lg text-white underline underline-offset-2" @click="refresh">
            Повторить
          </button>
        </template>

        <p v-else-if="!walk" class="font-body-md text-body-md text-white/75">Загружаю карту группы…</p>

        <template v-else-if="walk.status === 'finished'">
          <div class="flex items-center gap-space-sm">
            <span class="flex h-10 w-10 items-center justify-center rounded-full bg-tertiary text-on-tertiary">
              <MsIcon name="celebration" :size="22" />
            </span>
            <div class="flex flex-col">
              <p class="font-headline-sm text-headline-sm text-white">Экскурсия завершена</p>
              <p class="font-body-sm text-body-sm text-white/75">Спасибо, что были с группой</p>
            </div>
          </div>
          <button
            type="button"
            class="h-11 rounded-full bg-primary-container font-label-lg text-label-lg text-white shadow-stamp transition-colors hover:bg-primary active:scale-[0.98]"
            @click="back"
          >
            К экскурсии
          </button>
        </template>

        <template v-else-if="walk.status !== 'walking' || !destination">
          <p class="font-body-md text-body-md text-white/75">
            Группа ещё не вышла — карта откроется сама, как только краевед поведёт всех к месту.
          </p>
        </template>

        <template v-else>
          <div class="flex items-start gap-space-sm">
            <span
              class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full"
              :class="arrived ? 'bg-tertiary text-on-tertiary' : 'bg-primary-container text-white'"
            >
              <MsIcon :name="arrived ? 'where_to_vote' : 'flag'" :size="22" />
            </span>
            <div class="flex min-w-0 flex-1 flex-col">
              <p class="truncate font-headline-sm text-headline-sm text-white">
                {{ destination.name || 'Памятное место' }}
              </p>
              <p class="font-label-lg text-label-lg" :class="arrived ? 'text-tertiary-fixed-dim' : 'text-white'">
                {{ summary }}
              </p>
              <p class="font-body-sm text-body-sm text-white/75">{{ guideHint }}</p>
            </div>
          </div>

          <p v-if="actionError" class="rounded-xl bg-error/90 px-space-sm py-2 font-body-sm text-body-sm text-white" role="alert">
            {{ actionError }}
          </p>

          <div class="flex gap-space-xs">
            <button
              type="button"
              class="flex h-11 flex-1 items-center justify-center gap-space-xs rounded-full bg-primary-container font-label-lg text-label-lg text-white shadow-stamp transition-colors hover:bg-primary active:scale-[0.98]"
              @click="openNavigator"
            >
              <MsIcon name="navigation" :size="18" />
              Навигатор
            </button>
            <button
              v-if="isGuide"
              type="button"
              class="flex h-11 flex-1 items-center justify-center gap-space-xs rounded-full border border-white/20 bg-white/10 font-label-lg text-label-lg text-white backdrop-blur-sm transition-colors hover:bg-white/20 active:scale-[0.98] disabled:opacity-60"
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
            :class="confirmFinish ? 'bg-error text-white' : 'text-white/75 hover:text-white'"
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
