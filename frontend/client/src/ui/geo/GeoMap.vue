<script setup lang="ts">
import 'leaflet/dist/leaflet.css'

import L from 'leaflet'
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'

import { OREL_CENTER, TILES, type GeoMarker, type GeoPath, type GeoTone, type LatLon, type UserPosition } from '@/core/geo'
import MsIcon from '@/ui/MsIcon.vue'

/**
 * Гео-карта на Leaflet: подложка, метки, линии маршрутов, «где я».
 *
 * Карта не знает предметной области: окно само решает, какие у него метки и
 * какого они цвета, и отдаёт их пропсами. Сменить движок (MapLibre, 2ГИС) —
 * значит переписать только этот компонент.
 *
 * Метки — HTML-иконки с классами Tailwind, линии — SVG с классом `stroke-*`:
 * цвета берутся из палитры, как у остальной вёрстки, а не из hex в коде.
 */
const props = withDefaults(
  defineProps<{
    markers: GeoMarker[]
    paths?: GeoPath[]
    user?: UserPosition | null
    /** Идёт определение местоположения — кнопка «Где я» крутится. */
    locating?: boolean
    /** Подпись в углу карты. */
    label?: string
    /** Куда смотреть, пока меток нет. */
    center?: LatLon
  }>(),
  { paths: () => [], user: null, locating: false, label: undefined, center: () => OREL_CENTER },
)

const selected = defineModel<string | null>('selected', { default: null })

const emit = defineEmits<{ locate: [] }>()

const PIN_TONES: Record<GeoTone, string> = {
  primary: 'bg-primary text-on-primary',
  secondary: 'bg-secondary text-on-secondary',
  tertiary: 'bg-tertiary text-on-tertiary',
  neutral: 'bg-inverse-surface text-inverse-on-surface',
}

const PATH_TONES: Record<GeoTone, string> = {
  primary: 'stroke-primary',
  secondary: 'stroke-secondary',
  tertiary: 'stroke-tertiary',
  neutral: 'stroke-inverse-surface',
}

const HTML_ESCAPES: Record<string, string> = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }

/** Подписи приходят из сервиса — в HTML иконки они попадают только экранированными. */
function escapeHtml(text: string): string {
  return text.replace(/[&<>"']/g, (char) => HTML_ESCAPES[char] ?? char)
}

function pinIcon(marker: GeoMarker, active: boolean): L.DivIcon {
  const size = active ? 'h-12 w-12' : 'h-9 w-9'
  const glyph = marker.badge
    ? `<span class="font-label-lg text-label-lg">${escapeHtml(marker.badge)}</span>`
    : `<span class="material-symbols-outlined${active ? ' icon-filled' : ''}" style="font-size:${active ? 24 : 18}px" aria-hidden="true">${escapeHtml(marker.icon)}</span>`
  const caption = active
    ? `<span class="mt-1 max-w-48 truncate rounded-full bg-surface-container-lowest px-2.5 py-0.5 font-label-sm text-label-sm text-on-surface shadow-md">${escapeHtml(marker.label)}</span>`
    : ''
  return L.divIcon({
    className: 'geo-pin',
    iconSize: [0, 0],
    html:
      `<div class="geo-pin__body${active ? ' geo-pin__body--active' : ''}">` +
      `<span class="flex ${size} items-center justify-center rounded-full shadow-lg ring-4 ring-surface-container-lowest ${PIN_TONES[marker.tone]}">${glyph}</span>` +
      `${caption}</div>`,
  })
}

const USER_ICON = L.divIcon({
  className: 'geo-pin',
  iconSize: [0, 0],
  html:
    '<div class="geo-pin__body geo-pin__body--user">' +
    '<span class="flex h-5 w-5 items-center justify-center rounded-full bg-surface-container-lowest shadow-md">' +
    '<span class="h-3 w-3 rounded-full bg-secondary"></span></span></div>',
})

const container = ref<HTMLDivElement | null>(null)

let map: L.Map | null = null
let resizeObserver: ResizeObserver | null = null
const pathLayer = L.layerGroup()
const userLayer = L.layerGroup()
const markerLayer = L.layerGroup()
const markerById = new Map<string, L.Marker>()

/** Карта уже подогнана под метки — дальше вид не дёргаем, человек мог сам его сдвинуть. */
let framed = false
/** Нажали «Где я»: как только придёт место — перелететь к нему. */
let followUser = false

function renderMarkers(): void {
  markerLayer.clearLayers()
  markerById.clear()
  for (const item of props.markers) {
    const active = item.id === selected.value
    const marker = L.marker([item.lat, item.lon], {
      icon: pinIcon(item, active),
      title: item.label,
      riseOnHover: true,
      zIndexOffset: active ? 1000 : 0,
    })
    marker.on('click', () => (selected.value = item.id))
    marker.addTo(markerLayer)
    markerById.set(item.id, marker)
  }
}

function refreshPin(id: string | null): void {
  if (!id) return
  const item = props.markers.find((marker) => marker.id === id)
  const marker = markerById.get(id)
  if (!item || !marker) return
  const active = id === selected.value
  marker.setIcon(pinIcon(item, active))
  marker.setZIndexOffset(active ? 1000 : 0)
}

function renderPaths(): void {
  pathLayer.clearLayers()
  for (const path of props.paths) {
    if (path.points.length < 2) continue
    L.polyline(
      path.points.map((point): L.LatLngTuple => [point.lat, point.lon]),
      {
        className: PATH_TONES[path.tone],
        weight: 4,
        opacity: 0.9,
        lineCap: 'round',
        lineJoin: 'round',
        dashArray: path.dashed ? '10 9' : undefined,
        interactive: false,
      },
    ).addTo(pathLayer)
  }
}

function renderUser(): void {
  userLayer.clearLayers()
  const user = props.user
  if (!user) return
  const point: L.LatLngTuple = [user.lat, user.lon]
  L.circle(point, {
    radius: user.accuracyMeters,
    className: 'fill-secondary stroke-secondary',
    weight: 1,
    fillOpacity: 0.12,
    interactive: false,
  }).addTo(userLayer)
  L.marker(point, { icon: USER_ICON, interactive: false, keyboard: false, zIndexOffset: 500 }).addTo(userLayer)

  if (followUser && map) {
    followUser = false
    map.flyTo(point, Math.max(map.getZoom(), 15))
  }
}

/** Показать все метки и линии. Возвращает, было ли что показывать. */
function frameContent(): boolean {
  if (!map) return false
  const points: L.LatLngTuple[] = [
    ...props.markers.map((marker): L.LatLngTuple => [marker.lat, marker.lon]),
    ...props.paths.flatMap((path) => path.points.map((point): L.LatLngTuple => [point.lat, point.lon])),
  ]
  if (points.length === 0) {
    map.setView([props.center.lat, props.center.lon], 12)
    return false
  }
  if (points.length === 1) map.setView(points[0], 15)
  else map.fitBounds(L.latLngBounds(points), { padding: [48, 48], maxZoom: 16 })
  return true
}

function zoomIn(): void {
  map?.zoomIn()
}

function zoomOut(): void {
  map?.zoomOut()
}

function locate(): void {
  followUser = true
  // Место уже известно — перелетаем сразу, не дожидаясь нового фикса.
  if (props.user) renderUser()
  emit('locate')
}

onMounted(() => {
  if (!container.value) return
  map = L.map(container.value, {
    zoomControl: false,
    center: [props.center.lat, props.center.lon],
    zoom: 12,
  })
  map.attributionControl.setPrefix('<a href="https://leafletjs.com">Leaflet</a>')
  L.tileLayer(TILES.url, {
    attribution: TILES.attribution,
    maxZoom: TILES.maxZoom,
    className: 'geo-tiles',
  }).addTo(map)
  pathLayer.addTo(map)
  userLayer.addTo(map)
  markerLayer.addTo(map)

  renderPaths()
  renderMarkers()
  renderUser()
  framed = frameContent()

  // Контейнер меняет размер (поворот экрана, клавиатура) — без этого Leaflet рисует тайлы по старому размеру.
  resizeObserver = new ResizeObserver(() => map?.invalidateSize())
  resizeObserver.observe(container.value)
})

onBeforeUnmount(() => {
  resizeObserver?.disconnect()
  map?.remove()
  map = null
})

watch(
  () => props.markers,
  () => {
    renderMarkers()
    if (!framed) framed = frameContent()
  },
)

watch(
  () => props.paths,
  () => {
    renderPaths()
    if (!framed) framed = frameContent()
  },
)

watch(() => props.user, renderUser)

watch(selected, (id, previous) => {
  refreshPin(previous)
  refreshPin(id)
  const marker = id ? markerById.get(id) : undefined
  // Выбрали метку у края или за экраном (например, из списка) — подвинуть к ней.
  if (map && marker && !map.getBounds().pad(-0.2).contains(marker.getLatLng())) {
    map.panTo(marker.getLatLng())
  }
})
</script>

<template>
  <div class="relative isolate overflow-hidden bg-map-paper">
    <div ref="container" class="geo-map absolute inset-0" role="region" aria-label="Карта" />

    <div
      v-if="label"
      class="pointer-events-none absolute left-margin top-space-md z-[1000] flex max-w-[60%] items-center gap-1.5 rounded-full bg-surface-container-lowest/90 px-3 py-1.5 shadow-sm backdrop-blur-md"
    >
      <MsIcon name="nature" :size="16" class="shrink-0 text-secondary" />
      <span class="truncate font-label-sm text-label-sm font-medium text-on-surface-variant">{{ label }}</span>
    </div>

    <div class="absolute right-margin top-space-md z-[1000] flex flex-col gap-space-xs">
      <div class="flex flex-col items-center overflow-hidden rounded-full bg-surface-container-lowest/95 shadow-float backdrop-blur-md">
        <button
          type="button"
          aria-label="Приблизить"
          class="flex h-10 w-10 items-center justify-center text-on-surface transition-colors hover:bg-surface-container"
          @click="zoomIn"
        >
          <MsIcon name="add" :size="20" />
        </button>
        <div class="h-px w-5 bg-surface-container" />
        <button
          type="button"
          aria-label="Отдалить"
          class="flex h-10 w-10 items-center justify-center text-on-surface transition-colors hover:bg-surface-container"
          @click="zoomOut"
        >
          <MsIcon name="remove" :size="20" />
        </button>
      </div>
      <button
        type="button"
        aria-label="Показать все метки"
        class="flex h-10 w-10 items-center justify-center rounded-full bg-surface-container-lowest/95 text-on-surface shadow-float backdrop-blur-md transition-transform hover:scale-105"
        @click="frameContent"
      >
        <MsIcon name="fit_screen" :size="20" />
      </button>
      <button
        type="button"
        aria-label="Где я"
        class="flex h-10 w-10 items-center justify-center rounded-full bg-surface-container-lowest/95 text-secondary shadow-float backdrop-blur-md transition-transform hover:scale-105"
        @click="locate"
      >
        <MsIcon :name="locating ? 'progress_activity' : 'my_location'" :size="20" :class="{ 'animate-spin': locating }" />
      </button>
      <slot name="controls" />
    </div>

    <slot />
  </div>
</template>

<style>
/* Не scoped: разметку меток и тайлов создаёт Leaflet, до неё scoped-стили не дотянутся. */
.geo-map.leaflet-container {
  background: theme('colors.map.paper');
  font-family: inherit;
}

/* Лёгкая сепия — «военная картография» из кейса, без потери читаемости улиц. */
.geo-tiles {
  filter: sepia(0.2) saturate(0.9);
}

.geo-pin {
  background: none;
  border: 0;
}

/* Иконка нулевого размера, тело метки центрируется над точкой: так подпись любой длины не сдвигает остриё. */
.geo-pin__body {
  position: absolute;
  left: 0;
  top: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  white-space: nowrap;
  transform: translate(-50%, -18px);
}

.geo-pin__body--active {
  transform: translate(-50%, -24px);
}

.geo-pin__body--user {
  transform: translate(-50%, -10px);
}
</style>
