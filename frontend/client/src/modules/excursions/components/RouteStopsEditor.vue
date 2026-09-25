<script setup lang="ts">
import { computed, ref, watch } from 'vue'

import { plural } from '@/core/format'
import { distanceKm, formatDistance, type GeoMarker, type GeoPath, type LatLon } from '@/core/geo'
import MsIcon from '@/ui/MsIcon.vue'
import GeoMap from '@/ui/geo/GeoMap.vue'
import { FIELD_HINT_CLASS, INPUT_CLASS, TEXTAREA_CLASS } from '@/ui/form/styles'

import { MAX_STOPS, type StopDraft, type WalkTarget } from '../data'
import DestinationPicker from './DestinationPicker.vue'

/**
 * Маршрут экскурсии: точки, по которым краевед поведёт группу после сбора.
 * Добавить можно памятник со слоя «ВОВ» или любую точку тапом по карте —
 * у двора, где стоял штаб, памятника нет. Порядок — порядок прохода.
 */
const props = defineProps<{
  /** Место сбора — начало пути. `null` — ещё не выбрано. */
  start: (LatLon & { name: string }) | null
}>()

const model = defineModel<StopDraft[]>({ required: true })

/**
 * Своя копия списка. Модель — это проп: после записи в неё новое значение
 * приходит только с перерисовкой родителя, и вторая правка в том же такте
 * (название, а следом заметка) читала бы старый список и затирала первую.
 */
const stops = ref<StopDraft[]>(model.value)
watch(model, (value) => {
  if (value !== stops.value) stops.value = value
})
watch(stops, (value) => {
  if (value !== model.value) model.value = value
})

const picking = ref(false)
/** Ждём тапа по карте — следующая точка встанет туда. */
const placing = ref(false)
const selected = ref<string | null>(null)

const full = computed(() => stops.value.length >= MAX_STOPS)

const markers = computed<GeoMarker[]>(() => {
  const list: GeoMarker[] = stops.value.map((stop, index) => ({
    id: `stop-${index}`,
    lat: stop.lat,
    lon: stop.lon,
    label: stop.name || `Точка ${index + 1}`,
    icon: 'flag',
    tone: 'secondary',
    badge: String(index + 1),
  }))
  if (props.start) {
    list.unshift({ id: 'start', lat: props.start.lat, lon: props.start.lon, label: props.start.name || 'Место сбора', icon: 'groups', tone: 'primary' })
  }
  return list
})

const line = computed<LatLon[]>(() => [...(props.start ? [props.start] : []), ...stops.value])
const paths = computed<GeoPath[]>(() => (line.value.length > 1 ? [{ id: 'route', points: line.value, tone: 'secondary', dashed: true }] : []))

/** Путь по прямой между точками — пешком выйдет чуть больше, но порядок величины верный. */
const totalKm = computed(() => line.value.slice(1).reduce((sum, point, index) => sum + distanceKm(line.value[index], point), 0))

function legKm(index: number): number | null {
  const previous = index === 0 ? props.start : stops.value[index - 1]
  return previous ? distanceKm(previous, stops.value[index]) : null
}

const pickFrom = computed<LatLon>(() => stops.value.at(-1) ?? props.start ?? { lat: 52.9686, lon: 36.0694 })

function add(stop: StopDraft): void {
  if (full.value) return
  stops.value = [...stops.value, stop]
  selected.value = `stop-${stops.value.length - 1}`
}

function addFromList(target: WalkTarget): void {
  add({ name: target.name, lat: target.lat, lon: target.lon, poi_id: target.poi_id, note: '' })
  picking.value = false
}

function addFromMap(point: LatLon): void {
  if (!placing.value) return
  placing.value = false
  add({ name: '', lat: point.lat, lon: point.lon, poi_id: null, note: '' })
}

function update(index: number, patch: Partial<StopDraft>): void {
  stops.value = stops.value.map((stop, at) => (at === index ? { ...stop, ...patch } : stop))
}

function move(index: number, shift: -1 | 1): void {
  const target = index + shift
  if (target < 0 || target >= stops.value.length) return
  const next = [...stops.value]
  ;[next[index], next[target]] = [next[target], next[index]]
  stops.value = next
}

function remove(index: number): void {
  stops.value = stops.value.filter((_, at) => at !== index)
}
</script>

<template>
  <section class="flex flex-col gap-space-sm">
    <div class="relative">
      <GeoMap
        v-model:selected="selected"
        :markers="markers"
        :paths="paths"
        :center="start ?? undefined"
        class="h-52 w-full rounded-2xl shadow-document"
        @pick="addFromMap"
      />
      <!-- Режим «поставить точку»: подсказка поверх карты, пока не коснулись. -->
      <p
        v-if="placing"
        class="pointer-events-none absolute inset-x-space-sm top-space-sm rounded-xl bg-night/70 px-space-sm py-1.5 text-center font-label-md text-label-md text-white backdrop-blur-sm"
        role="status"
      >
        Коснитесь карты там, где будет точка
      </p>
    </div>

    <p :class="FIELD_HINT_CLASS">
      <template v-if="stops.length">
        {{ stops.length }} {{ plural(stops.length, ['точка', 'точки', 'точек']) }} после сбора
        <template v-if="start"> · ≈ {{ formatDistance(totalKm) }} по прямой</template>
      </template>
      <template v-else>Без маршрута экскурсия пройдёт на месте сбора. Добавьте точки, по которым поведёте группу.</template>
    </p>

    <ol v-if="stops.length" class="flex flex-col gap-space-xs">
      <li
        v-for="(stop, index) in stops"
        :key="index"
        class="flex flex-col gap-space-xs rounded-2xl bg-surface-container-lowest p-space-sm shadow-document ring-secondary/60"
        :class="{ 'ring-2': selected === `stop-${index}` }"
      >
        <div class="flex items-center gap-space-sm">
          <button
            type="button"
            class="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-secondary font-label-lg text-label-lg text-on-secondary"
            :aria-label="`Показать точку ${index + 1} на карте`"
            @click="selected = `stop-${index}`"
          >
            {{ index + 1 }}
          </button>
          <input
            :value="stop.name"
            type="text"
            maxlength="255"
            :placeholder="`Точка ${index + 1}: как называется место`"
            :aria-label="`Название точки ${index + 1}`"
            :class="[INPUT_CLASS, 'border-b border-outline-variant py-1.5 font-label-lg text-label-lg focus:border-primary']"
            @input="update(index, { name: ($event.target as HTMLInputElement).value })"
          />
          <div class="flex shrink-0 items-center">
            <button
              type="button"
              class="flex h-8 w-8 items-center justify-center rounded-full text-on-surface-variant hover:bg-surface-container disabled:opacity-30"
              :disabled="index === 0"
              :aria-label="`Точку ${index + 1} раньше`"
              @click="move(index, -1)"
            >
              <MsIcon name="arrow_upward" :size="18" />
            </button>
            <button
              type="button"
              class="flex h-8 w-8 items-center justify-center rounded-full text-on-surface-variant hover:bg-surface-container disabled:opacity-30"
              :disabled="index === stops.length - 1"
              :aria-label="`Точку ${index + 1} позже`"
              @click="move(index, 1)"
            >
              <MsIcon name="arrow_downward" :size="18" />
            </button>
            <button
              type="button"
              class="flex h-8 w-8 items-center justify-center rounded-full text-error hover:bg-error-container"
              :aria-label="`Убрать точку ${index + 1}`"
              @click="remove(index)"
            >
              <MsIcon name="close" :size="18" />
            </button>
          </div>
        </div>
        <p v-if="legKm(index) !== null" class="flex items-center gap-1 pl-12 font-label-sm text-label-sm text-on-surface-variant">
          <MsIcon name="directions_walk" :size="15" />
          {{ formatDistance(legKm(index) ?? 0) }} от {{ index === 0 ? 'места сбора' : `точки ${index}` }}
        </p>
        <textarea
          :value="stop.note"
          rows="2"
          maxlength="2000"
          placeholder="Что здесь рассказать или сделать: история места, задание группе"
          :aria-label="`Что рассказать на точке ${index + 1}`"
          :class="TEXTAREA_CLASS"
          @input="update(index, { note: ($event.target as HTMLTextAreaElement).value })"
        />
      </li>
    </ol>

    <div class="grid grid-cols-2 gap-space-xs">
      <button
        type="button"
        class="flex items-center justify-center gap-space-xs rounded-full bg-secondary-container px-space-sm py-2.5 font-label-md text-label-md text-on-secondary-container active:scale-95 disabled:opacity-50"
        :disabled="full"
        @click="picking = true"
      >
        <MsIcon name="account_balance" :size="18" />
        Памятное место
      </button>
      <button
        type="button"
        class="flex items-center justify-center gap-space-xs rounded-full px-space-sm py-2.5 font-label-md text-label-md active:scale-95 disabled:opacity-50"
        :class="placing ? 'bg-secondary text-on-secondary' : 'bg-surface-container-high text-on-surface'"
        :disabled="full"
        :aria-pressed="placing"
        @click="placing = !placing"
      >
        <MsIcon :name="placing ? 'close' : 'add_location_alt'" :size="18" />
        {{ placing ? 'Отменить' : 'Точка на карте' }}
      </button>
    </div>
    <p v-if="full" :class="FIELD_HINT_CLASS">В маршруте уже {{ MAX_STOPS }} точек — больше в одну экскурсию не поместится.</p>

    <DestinationPicker
      v-if="picking"
      :from="pickFrom"
      :stops="[]"
      title="Точка маршрута"
      subtitle="Встанет в конец маршрута — порядок потом можно поменять"
      @close="picking = false"
      @pick="addFromList"
    />
  </section>
</template>
