<script setup lang="ts">
import { computed, ref, watch } from 'vue'

import { useAsync } from '@/core/async'
import { useGeolocation, type GeoMarker } from '@/core/geo'
import { useSessionStore } from '@/core/session'
import GeoMap from '@/ui/geo/GeoMap.vue'
import MsIcon from '@/ui/MsIcon.vue'
import StateBlock from '@/ui/StateBlock.vue'

import AccountRequired from './components/AccountRequired.vue'
import ExcursionCard from './components/ExcursionCard.vue'
import { fetchExcursions, fetchMyExcursions, isGuideRole, type Excursion } from './data'

type Tab = 'upcoming' | 'mine'

const session = useSessionStore()
const { position: userPosition, status: geoStatus, start: startLocating } = useGeolocation()

const tab = ref<Tab>('upcoming')
const selectedId = ref<string | null>(null)

const { data, loading, error, retry } = useAsync(load)

async function load(): Promise<Excursion[]> {
  if (tab.value === 'upcoming') return fetchExcursions(session.hasAccount)
  if (!session.hasAccount) return []
  const mine = await fetchMyExcursions()
  // Краевед может и вести свою экскурсию, и быть записан на чужую — дубли убираем.
  const byId = new Map([...mine.guiding, ...mine.joined].map((excursion) => [excursion.id, excursion]))
  return [...byId.values()].sort((a, b) => a.starts_at.localeCompare(b.starts_at))
}

watch(tab, () => {
  selectedId.value = null
  void retry()
})

const isGuide = computed(() => session.hasAccount && isGuideRole(session.user?.role))

const markers = computed<GeoMarker[]>(() =>
  (data.value ?? []).map((excursion) => ({
    id: excursion.id,
    lat: excursion.lat,
    lon: excursion.lon,
    label: excursion.title,
    icon: 'groups',
    tone: excursion.status === 'gathering' ? 'primary' : 'secondary',
  })),
)

/** Выбранная на карте экскурсия — первой в списке. */
const ordered = computed(() => {
  const items = data.value ?? []
  const selected = items.find((excursion) => excursion.id === selectedId.value)
  return selected ? [selected, ...items.filter((excursion) => excursion !== selected)] : items
})

const TABS: { value: Tab; title: string }[] = [
  { value: 'upcoming', title: 'Ближайшие' },
  { value: 'mine', title: 'Мои' },
]
</script>

<template>
  <div class="flex w-full flex-col gap-space-md px-margin pb-space-lg pt-space-xs">
    <section class="flex flex-col gap-space-xs rounded-2xl bg-secondary-container/60 p-space-md shadow-document">
      <p class="font-archival text-archival uppercase text-on-secondary-container">Экспедиция памяти</p>
      <h2
        class="ribbon-shimmer font-headline-sm text-headline-sm text-on-secondary-container [--shimmer-base:theme(colors.on-secondary-container)]"
      >
        Экскурсии с краеведами
      </h2>
      <p class="font-body-sm text-body-sm text-on-surface-variant">
        Запишитесь заранее, а на месте встряхните телефон вместе с краеведом — и вы в группе.
      </p>
      <RouterLink
        v-if="isGuide"
        :to="{ name: 'excursion-new' }"
        class="mt-space-xs inline-flex items-center gap-1.5 self-start rounded-full bg-primary-container px-space-md py-2 font-label-md text-label-md text-white shadow-stamp transition-colors hover:bg-primary active:scale-95"
      >
        <MsIcon name="add" :size="18" />
        Новая экскурсия
      </RouterLink>
    </section>

    <div class="relative grid grid-cols-2 rounded-full bg-surface-container-low p-1 text-center" role="tablist">
      <span
        class="absolute inset-y-1 left-1 w-[calc(50%-4px)] rounded-full bg-surface-container-lowest shadow-float transition-transform duration-300 ease-out"
        :class="tab === 'mine' ? 'translate-x-full' : 'translate-x-0'"
        aria-hidden="true"
      />
      <button
        v-for="item in TABS"
        :key="item.value"
        type="button"
        role="tab"
        :aria-selected="tab === item.value"
        class="relative z-10 rounded-full py-2 font-label-lg text-label-lg transition-colors duration-200"
        :class="tab === item.value ? 'text-on-surface' : 'text-on-surface-variant hover:text-on-surface'"
        @click="tab = item.value"
      >
        {{ item.title }}
      </button>
    </div>

    <AccountRequired v-if="tab === 'mine' && !session.hasAccount" text="Свои экскурсии видно после входа." />

    <StateBlock
      v-else
      :loading="loading"
      :error="error"
      :empty="!data?.length"
      empty-icon="groups"
      :empty-text="tab === 'mine' ? 'Вы пока не записаны ни на одну экскурсию' : 'Ближайших экскурсий пока нет'"
      @retry="retry"
    >
      <GeoMap
        v-model:selected="selectedId"
        :markers="markers"
        :user="userPosition"
        :locating="geoStatus === 'locating'"
        class="h-60 w-full rounded-2xl shadow-document short:h-44"
        @locate="startLocating"
      />

      <ul class="flex flex-col gap-space-sm">
        <li v-for="excursion in ordered" :key="excursion.id">
          <ExcursionCard :excursion="excursion" :selected="excursion.id === selectedId" />
        </li>
      </ul>
    </StateBlock>
  </div>
</template>
