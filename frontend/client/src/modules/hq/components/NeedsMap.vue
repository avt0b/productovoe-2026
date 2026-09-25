<script setup lang="ts">
import { computed, nextTick, ref } from 'vue'

import { formatMoney, plural } from '@/core/format'
import { distanceKm, formatDistance, geolocationProblem, useGeolocation, type GeoMarker } from '@/core/geo'
import InlineNotice from '@/ui/InlineNotice.vue'
import MsIcon from '@/ui/MsIcon.vue'
import StateBlock from '@/ui/StateBlock.vue'
import GeoMap from '@/ui/geo/GeoMap.vue'

import {
  CAMPAIGN_KINDS,
  NEED_KINDS,
  campaignOf,
  contactLink,
  squadPlace,
  tripDay,
  type Need,
  type Squad,
  type Trip,
} from '../data'

/**
 * Карта потребностей отрядов из кейса: где какой отряд и что ему нужно —
 * люди на раскопки, деньги на ГСМ, снаряжение. Отряд без узнаваемого города
 * на карту не попадает, но остаётся в списке под ней.
 */
const props = defineProps<{
  squads: Squad[]
  needs: Need[]
  /** Ближайший выезд каждого отряда. */
  nextTrips: Map<string, Trip>
}>()

const emit = defineEmits<{ donate: [need: Need]; trip: [tripId: string] }>()

const { position, status: geoStatus, start: locate } = useGeolocation()
const geoProblem = computed(() => geolocationProblem(geoStatus.value))

/** Пока не знаем, где человек, первыми идут отряды, которым нужнее; узнали — ближние. */
const rows = computed(() => {
  const bySquad = new Map<string, Need[]>()
  for (const need of props.needs) bySquad.set(need.squad_id, [...(bySquad.get(need.squad_id) ?? []), need])
  const origin = position.value
  return props.squads
    .map((squad) => {
      const place = squadPlace(squad)
      return { squad, needs: bySquad.get(squad.id) ?? [], place, km: origin && place ? distanceKm(origin, place) : null }
    })
    .sort((a, b) => {
      if (origin) return (a.km ?? Infinity) - (b.km ?? Infinity)
      return b.needs.length - a.needs.length
    })
})

/**
 * Отряды одного города разводим по кругу, иначе метки лягут одна на другую.
 * Порядок — как пришли из сервиса, а не как в списке: иначе при определении
 * места метки соседей поменялись бы местами.
 */
const markers = computed<GeoMarker[]>(() => {
  const taken = new Map<string, number>()
  const order = new Map(props.squads.map((squad, index) => [squad.id, index]))
  const stable = [...rows.value].sort((a, b) => (order.get(a.squad.id) ?? 0) - (order.get(b.squad.id) ?? 0))
  return stable.flatMap(({ squad, needs, place }) => {
    if (!place) return []
    const key = `${place.lat},${place.lon}`
    const index = taken.get(key) ?? 0
    taken.set(key, index + 1)
    const angle = index * 2.4
    const shift = index ? 0.015 : 0
    return [
      {
        id: squad.id,
        lat: place.lat + Math.sin(angle) * shift,
        lon: place.lon + Math.cos(angle) * shift * 1.6,
        label: squad.name,
        icon: 'flag',
        tone: needs.length ? 'secondary' : 'neutral',
        badge: needs.length ? String(needs.length) : undefined,
      },
    ]
  })
})

const selectedId = ref<string | null>(rows.value.find((row) => row.needs.length && row.place)?.squad.id ?? rows.value[0]?.squad.id ?? null)
const selected = computed(() => rows.value.find((row) => row.squad.id === selectedId.value) ?? null)
const selectedTrip = computed(() => (selected.value ? (props.nextTrips.get(selected.value.squad.id) ?? null) : null))
const selectedTripLabel = computed(() => {
  if (!selectedTrip.value) return ''
  const day = tripDay(selectedTrip.value.starts_on)
  return `К выезду ${day.day} ${day.month}`
})
const selectedContact = computed(() => contactLink(selected.value?.squad.contact ?? ''))

const panel = ref<HTMLElement | null>(null)

async function pick(squadId: string): Promise<void> {
  selectedId.value = squadId
  await nextTick()
  panel.value?.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
}

function needTitle(need: Need): string {
  return need.kind === 'funds' ? campaignOf(need).headline : need.title
}

function needIcon(need: Need): string {
  return need.kind === 'funds' ? CAMPAIGN_KINDS[campaignOf(need).kind].icon : NEED_KINDS[need.kind].icon
}

function progress(need: Need): number | null {
  return need.target_amount ? Math.min(100, Math.round((need.collected_amount / need.target_amount) * 100)) : null
}
</script>

<template>
  <div class="flex flex-col gap-space-md">
    <StateBlock v-if="!rows.length" :loading="false" :error="null" empty empty-icon="groups" empty-text="Отрядов в штабе пока нет" />

    <template v-else>
      <Transition appear name="map-in">
        <GeoMap
          v-model:selected="selectedId"
          :markers="markers"
          :user="position"
          :locating="geoStatus === 'locating'"
          label="Отряды · по городу штаба"
          class="h-72 rounded-2xl shadow-document short:h-56"
          @locate="locate"
        />
      </Transition>
      <InlineNotice v-if="geoProblem" tone="error" icon="location_off">{{ geoProblem }}</InlineNotice>

      <article
        v-if="selected"
        ref="panel"
        class="flex scroll-mt-space-md flex-col gap-space-sm rounded-2xl bg-surface-container-lowest p-space-md shadow-document"
        aria-live="polite"
      >
        <div class="flex items-start gap-space-sm">
          <span
            class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-secondary-container text-on-secondary-container"
            aria-hidden="true"
          >
            <MsIcon name="flag" :size="20" filled />
          </span>
          <div class="flex min-w-0 flex-1 flex-col">
            <p class="font-archival text-archival uppercase text-on-surface-variant">{{ selected.squad.region || 'Город не указан' }}</p>
            <h3 class="font-headline-sm text-headline-sm text-on-surface">{{ selected.squad.name }}</h3>
            <p v-if="selected.squad.description" class="font-body-sm text-body-sm text-on-surface-variant">{{ selected.squad.description }}</p>
          </div>
        </div>

        <ul v-if="selected.needs.length" class="flex flex-col divide-y divide-outline-variant/60">
          <li v-for="need in selected.needs" :key="need.id" class="flex items-center gap-space-sm py-2">
            <MsIcon :name="needIcon(need)" :size="18" class="shrink-0 text-secondary" />
            <div class="flex min-w-0 flex-1 flex-col gap-0.5">
              <p class="truncate font-label-md text-label-md text-on-surface">{{ needTitle(need) }}</p>
              <template v-if="need.kind === 'funds' && progress(need) !== null">
                <div class="h-1 w-full overflow-hidden rounded-full bg-surface-container-high" aria-hidden="true">
                  <div class="h-full rounded-full bg-secondary" :style="{ width: `${progress(need)}%` }" />
                </div>
                <p class="font-label-sm text-label-sm text-on-surface-variant">
                  {{ formatMoney(need.collected_amount) }} из {{ formatMoney(need.target_amount) }}
                </p>
              </template>
              <p v-else class="font-label-sm text-label-sm text-on-surface-variant">{{ NEED_KINDS[need.kind].title }}</p>
            </div>
            <button
              v-if="need.kind === 'funds'"
              type="button"
              class="shrink-0 rounded-full bg-secondary px-space-sm py-1.5 font-label-md text-label-md text-on-secondary active:scale-95"
              @click="emit('donate', need)"
            >
              Помочь
            </button>
          </li>
        </ul>
        <p v-else class="font-body-sm text-body-sm text-on-surface-variant">Сейчас отряду ничего не нужно — спасибо всем, кто помог.</p>

        <div v-if="selectedTrip || selectedContact" class="flex flex-wrap gap-space-xs">
          <button
            v-if="selectedTrip"
            type="button"
            class="flex items-center gap-space-xs rounded-full bg-surface-container-high px-space-md py-2 font-label-md text-label-md text-on-surface active:scale-95"
            @click="emit('trip', selectedTrip.id)"
          >
            <MsIcon name="event" :size="18" />
            {{ selectedTripLabel }}
          </button>
          <a
            v-if="selectedContact"
            :href="selectedContact.href"
            target="_blank"
            rel="noopener"
            class="flex items-center gap-space-xs rounded-full bg-surface-container-high px-space-md py-2 font-label-md text-label-md text-on-surface active:scale-95"
          >
            <MsIcon :name="selectedContact.icon" :size="18" />
            {{ selectedContact.label }}
          </a>
        </div>
        <p v-if="!selectedContact && selected.squad.contact" class="flex items-center gap-space-xs font-body-sm text-body-sm text-on-surface-variant">
          <MsIcon name="contact_phone" :size="18" class="shrink-0" />
          {{ selected.squad.contact }}
        </p>
      </article>

      <section class="flex flex-col gap-space-xs">
        <p class="font-archival text-archival uppercase text-on-surface-variant">Все отряды · {{ rows.length }}</p>
        <ul class="flex flex-col gap-space-xs">
          <li v-for="{ squad, needs, place, km } in rows" :key="squad.id">
            <button
              type="button"
              class="flex w-full items-center gap-space-sm rounded-2xl p-space-sm text-left transition-colors duration-200 active:scale-[0.99]"
              :class="squad.id === selectedId ? 'bg-surface-container-lowest shadow-document' : 'hover:bg-surface-container-low'"
              :aria-current="squad.id === selectedId ? 'true' : undefined"
              @click="pick(squad.id)"
            >
              <span
                class="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-surface-container-high text-on-surface-variant"
                aria-hidden="true"
              >
                <MsIcon :name="place ? 'flag' : 'wrong_location'" :size="18" />
              </span>
              <span class="flex min-w-0 flex-1 flex-col">
                <span class="truncate font-label-lg text-label-lg text-on-surface">{{ squad.name }}</span>
                <span class="truncate font-body-sm text-body-sm text-on-surface-variant">
                  {{ [squad.region, km !== null ? formatDistance(km) : '', place ? '' : 'нет на карте'].filter(Boolean).join(' · ') || 'Город не указан' }}
                </span>
              </span>
              <span
                v-if="needs.length"
                class="shrink-0 rounded-full bg-secondary-container px-2 py-0.5 font-label-sm text-label-sm text-on-secondary-container"
              >
                {{ needs.length }} {{ plural(needs.length, ['нужда', 'нужды', 'нужд']) }}
              </span>
            </button>
          </li>
        </ul>
      </section>
    </template>
  </div>
</template>

<style scoped>
/* Карта — не мгновенно, а проявляется: заметнее на первом открытии экрана, чем резкий скачок плиток. */
.map-in-enter-active {
  transition:
    opacity 320ms ease-out,
    transform 320ms cubic-bezier(0.22, 1, 0.36, 1);
}
.map-in-enter-from {
  opacity: 0;
  transform: scale(0.97);
}

@media (prefers-reduced-motion: reduce) {
  .map-in-enter-active {
    transition: opacity 150ms linear;
  }
  .map-in-enter-from {
    transform: none;
  }
}
</style>
