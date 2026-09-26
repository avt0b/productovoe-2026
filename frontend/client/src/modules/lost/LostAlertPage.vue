<script setup lang="ts">
import { computed } from 'vue'

import type { GeoMarker, GeoPath, LatLon } from '@/core/geo'
import StateBlock from '@/ui/StateBlock.vue'
import GeoMap from '@/ui/geo/GeoMap.vue'
import MsIcon from '@/ui/MsIcon.vue'

import ClosedPanel from './components/ClosedPanel.vue'
import LostPanel from './components/LostPanel.vue'
import WatcherPanel from './components/WatcherPanel.vue'
import { useLostAlert } from './useLostAlert'

/**
 * Экран поиска потерявшегося. Вёрстка — как прогулка (`WalkPage`): карта на весь
 * экран, круглая «Назад» и пилюля статуса сверху, тёмная стеклянная карточка
 * снизу. Вся логика — в `useLostAlert`, здесь только карта и выбор карточки.
 */
const props = defineProps<{ alertId: string }>()

const lost = useLostAlert(props.alertId)
const { alert, loading, loadError, offline, role, active, geo, pointRoute } = lost

const statusLabel = computed(() => {
  const status = alert.value?.status
  if (status === 'found') return 'Нашлись'
  if (status === 'cancelled') return 'Отбой'
  if (status === 'expired') return 'Поиск закрыт'
  return 'Идёт поиск'
})

/** Метки: потерявшийся и ищущие с точками, кроме меня (меня рисует проп user). */
const markers = computed<GeoMarker[]>(() => {
  const current = alert.value
  if (!current) return []
  const list: GeoMarker[] = []
  const lp = current.lost.position
  if (lp && !current.lost.is_me) {
    list.push({ id: `lost-${current.lost.user_id}`, lat: lp.lat, lon: lp.lon, label: current.lost.display_name, icon: 'sos', tone: 'primary' })
  }
  for (const w of current.watchers) {
    if (w.is_me || !w.position) continue
    const icon = w.responding ? 'directions_run' : w.relation === 'guide' ? 'record_voice_over' : 'person'
    list.push({
      id: `watcher-${w.user_id}`,
      lat: w.position.lat,
      lon: w.position.lon,
      label: `${w.display_name}${w.responding ? ' · идёт' : ''}`,
      icon,
      tone: 'secondary',
    })
  }
  return list
})

const paths = computed<GeoPath[]>(() => (pointRoute.path.value ? [pointRoute.path.value] : []))

/** Сначала показать меня и потерявшегося вместе, дальше — вид маршрута. */
const focus = computed(() => {
  if (pointRoute.focus.value) return pointRoute.focus.value
  const me = geo.position.value
  const lp = alert.value?.lost.position
  const points: LatLon[] = []
  if (me) points.push({ lat: me.lat, lon: me.lon })
  if (lp && !alert.value?.lost.is_me) points.push({ lat: lp.lat, lon: lp.lon })
  return points.length ? { key: props.alertId, points } : null
})

const following = computed(() => pointRoute.state.value === 'active' || pointRoute.state.value === 'arrived')
</script>

<template>
  <div class="fixed inset-0 z-0 flex flex-col bg-surface">
    <div class="absolute inset-0">
      <GeoMap
        class="h-full w-full"
        :markers="markers"
        :paths="paths"
        :user="geo.position.value"
        :locating="geo.status.value === 'locating'"
        :focus="focus"
        :follow="following"
      />
    </div>

    <!-- Верх: назад и статус поиска. -->
    <div class="pointer-events-none relative z-10 flex items-center gap-space-sm px-space-sm pt-safe">
      <button
        type="button"
        aria-label="Назад"
        class="pointer-events-auto mt-space-sm flex h-11 w-11 items-center justify-center rounded-full border border-white/15 bg-night/55 text-white shadow-sheet backdrop-blur-md transition-colors hover:bg-night/70 active:scale-95"
        @click="lost.back()"
      >
        <MsIcon name="arrow_back" :size="22" />
      </button>
      <div class="pointer-events-auto mt-space-sm flex min-w-0 items-center gap-space-xs rounded-full border border-white/15 bg-night/55 px-space-md py-2 shadow-sheet backdrop-blur-md">
        <span
          class="h-2 w-2 shrink-0 rounded-full"
          :class="active ? 'animate-pulse bg-error' : 'bg-tertiary-fixed-dim'"
        />
        <span class="truncate font-label-lg text-label-lg text-white">{{ statusLabel }}</span>
      </div>
    </div>

    <!-- Низ: карточка по состоянию. -->
    <div class="pointer-events-none absolute inset-x-0 bottom-0 z-10 px-space-sm pb-safe">
      <div class="pointer-events-auto mb-space-sm flex flex-col gap-space-sm rounded-2xl border border-white/15 bg-night/55 p-space-md shadow-sheet backdrop-blur-md">
        <StateBlock
          v-if="loading || loadError"
          :loading="loading"
          :error="loadError"
          @retry="() => {}"
        />
        <template v-else-if="alert">
          <p
            v-if="offline"
            class="font-body-sm text-body-sm text-white/60"
          >
            Нет связи — показываем последнее известное
          </p>

          <ClosedPanel v-if="!active" :lost="lost" />
          <WatcherPanel v-else-if="role === 'watcher'" :lost="lost" />
          <LostPanel v-else-if="role === 'lost'" :lost="lost" />
          <p v-else class="font-body-md text-body-md text-white/75">
            Вы видите поиск как администратор.
          </p>
        </template>
      </div>
    </div>
  </div>
</template>
