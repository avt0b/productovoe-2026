<script setup lang="ts">
import 'leaflet/dist/leaflet.css'

import { App } from '@capacitor/app'
import type { PluginListenerHandle } from '@capacitor/core'
import L from 'leaflet'
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'

import { OREL_CENTER, TILES, type GeoMarker, type GeoPath, type GeoTone, type LatLon, type UserPosition } from '@/core/geo'
import MsIcon from '@/ui/MsIcon.vue'

import type { GeoCircle } from './circles'

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
    /** Радиусы вокруг точек: «в 5 км от вас», зона работ, радиус сбора. */
    circles?: GeoCircle[]
    user?: UserPosition | null
    /** Идёт определение местоположения — кнопка «Где я» крутится. */
    locating?: boolean
    /** Подпись в углу карты. */
    label?: string
    /** Куда смотреть, пока меток нет. */
    center?: LatLon
    /**
     * Режим навигации: человек идёт, и карта держит его в кадре. Пока он
     * внутри видимой области, вид не двигается — можно разглядывать маршрут;
     * подошёл к краю — карта подвинется. Сдвинул карту пальцем — следование
     * выключается до «Где я»: отбирать у человека карту нельзя.
     */
    follow?: boolean
    /**
     * Карта в списке — превью: она не перехватывает прокрутку страницы, а по
     * нажатию разворачивается на весь экран. Маленькая карта, которая ловит
     * палец вместо страницы, — главная беда карт в ленте.
     *
     * Экранам, где по карте ставят точку (`pick`), это не нужно: там нажатие
     * уже занято.
     */
    expandable?: boolean
  }>(),
  {
    paths: () => [],
    circles: () => [],
    user: null,
    locating: false,
    label: undefined,
    center: () => OREL_CENTER,
    follow: false,
    expandable: false,
  },
)

const selected = defineModel<string | null>('selected', { default: null })

/** `pick` — тап по пустому месту карты: окно может взять эту точку (новое место «Последнего боя»). */
const emit = defineEmits<{ locate: []; pick: [point: LatLon] }>()

const PIN_TONES: Record<GeoTone, string> = {
  primary: 'bg-primary text-on-primary',
  secondary: 'bg-secondary text-on-secondary',
  tertiary: 'bg-tertiary text-on-tertiary',
  neutral: 'bg-inverse-surface text-inverse-on-surface',
}

const CIRCLE_TONES: Record<GeoTone, string> = {
  primary: 'fill-primary stroke-primary',
  secondary: 'fill-secondary stroke-secondary',
  tertiary: 'fill-tertiary stroke-tertiary',
  neutral: 'fill-inverse-surface stroke-inverse-surface',
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

/** Карта раскрыта на весь экран. */
const expanded = ref(false)
/** Превью: жесты выключены, нажатие разворачивает. */
const preview = computed(() => props.expandable && !expanded.value)

let map: L.Map | null = null
let resizeObserver: ResizeObserver | null = null
const circleLayer = L.layerGroup()
const pathLayer = L.layerGroup()
const userLayer = L.layerGroup()
const markerLayer = L.layerGroup()
const markerById = new Map<string, L.Marker>()

/** Карта уже подогнана под метки — дальше вид не дёргаем, человек мог сам его сдвинуть. */
let framed = false
/** Нажали «Где я»: как только придёт место — перелететь к нему. */
let followUser = false
/** Следование в режиме навигации включено: человек не сдвигал карту сам. */
let navigating = props.follow

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

function renderCircles(): void {
  circleLayer.clearLayers()
  for (const circle of props.circles) {
    L.circle([circle.lat, circle.lon], {
      radius: circle.radiusMeters,
      className: CIRCLE_TONES[circle.tone ?? 'primary'],
      weight: 1.5,
      fillOpacity: 0.1,
      dashArray: circle.dashed ? '8 8' : undefined,
      interactive: false,
    }).addTo(circleLayer)
  }
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
    return
  }
  // Навигация: человек дошёл до края видимой области — подвинуть карту к нему.
  if (props.follow && navigating && map && !map.getBounds().pad(-0.25).contains(point)) {
    map.panTo(point)
  }
}

/** Показать все метки и линии. Возвращает, было ли что показывать. */
function frameContent(): boolean {
  if (!map) return false
  const points: L.LatLngTuple[] = [
    ...props.markers.map((marker): L.LatLngTuple => [marker.lat, marker.lon]),
    ...props.paths.flatMap((path) => path.points.map((point): L.LatLngTuple => [point.lat, point.lon])),
    // Окружность показываем целиком: иначе «в 5 км от вас» упирается в край экрана.
    ...props.circles.flatMap((circle) => {
      const box = L.latLng(circle.lat, circle.lon).toBounds(circle.radiusMeters * 2)
      return [box.getSouthWest(), box.getNorthEast()].map((corner): L.LatLngTuple => [corner.lat, corner.lng])
    }),
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

/**
 * Жесты карты. В превью они выключены: палец должен прокручивать страницу, а
 * не таскать карту, которая всё равно размером с ладонь.
 */
function setInteractive(on: boolean): void {
  if (!map) return
  for (const handler of [map.dragging, map.touchZoom, map.doubleClickZoom, map.scrollWheelZoom, map.boxZoom, map.keyboard]) {
    if (on) handler.enable()
    else handler.disable()
  }
}

let backHandle: PluginListenerHandle | null = null
/** Подписка на «назад» ещё нужна: карту могли свернуть раньше, чем подписка завелась. */
let backWanted = false

function onKey(event: KeyboardEvent): void {
  if (event.key === 'Escape') collapse()
}

function expand(): void {
  if (expanded.value) return
  expanded.value = true
  document.body.style.overflow = 'hidden'
  window.addEventListener('keydown', onKey)
  backWanted = true
  // В приложении карту закрывают аппаратной кнопкой «назад», а не крестиком.
  void App.addListener('backButton', () => collapse()).then((handle) => {
    if (backWanted) backHandle = handle
    else void handle.remove()
  })
  void nextTick(() => {
    setInteractive(true)
    map?.invalidateSize()
    frameContent()
  })
}

function collapse(): void {
  if (!expanded.value) return
  expanded.value = false
  document.body.style.overflow = ''
  window.removeEventListener('keydown', onKey)
  backWanted = false
  void backHandle?.remove()
  backHandle = null
  void nextTick(() => {
    setInteractive(false)
    map?.invalidateSize()
    frameContent()
  })
}

function locate(): void {
  followUser = true
  navigating = props.follow
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
  circleLayer.addTo(map)
  pathLayer.addTo(map)
  userLayer.addTo(map)
  markerLayer.addTo(map)
  // Клик по метке до карты не доходит — сюда попадает только пустое место.
  map.on('click', (event: L.LeafletMouseEvent) => {
    if (preview.value) return expand()
    emit('pick', { lat: event.latlng.lat, lon: event.latlng.lng })
  })
  // Сдвинул карту сам — значит, смотрит куда-то ещё: не тянуть вид обратно.
  map.on('dragstart', () => (navigating = false))

  if (preview.value) setInteractive(false)

  renderCircles()
  renderPaths()
  renderMarkers()
  renderUser()
  framed = frameContent()

  // Контейнер меняет размер (поворот экрана, клавиатура) — без этого Leaflet рисует тайлы по старому размеру.
  resizeObserver = new ResizeObserver(() => map?.invalidateSize())
  resizeObserver.observe(container.value)
})

onBeforeUnmount(() => {
  // Экран ушёл с раскрытой картой — вернуть странице прокрутку и снять подписки.
  if (expanded.value) collapse()
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

watch(
  () => props.circles,
  () => {
    renderCircles()
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
    <!-- Раскрытая карта уезжает в body: внутри карточки с тенью и своим
         overflow `fixed` отсчитывался бы от карточки, а не от окна. Место в
         потоке остаётся за корнем — страница под ней не прыгает. -->
    <Teleport to="body" :disabled="!expanded">
      <div :class="expanded ? 'fixed inset-0 z-50 bg-map-paper' : 'absolute inset-0'">
        <div ref="container" class="geo-map absolute inset-0" role="region" aria-label="Карта" />

        <div
          v-if="label"
          class="pointer-events-none absolute left-margin top-space-md z-[1000] max-w-[60%]"
          :class="{ 'pt-safe': expanded }"
        >
          <div class="flex items-center gap-1.5 rounded-full bg-surface-container-lowest/90 px-3 py-1.5 shadow-sm backdrop-blur-md">
            <MsIcon name="nature" :size="16" class="shrink-0 text-secondary" />
            <span class="truncate font-label-sm text-label-sm font-medium text-on-surface-variant">{{ label }}</span>
          </div>
        </div>

        <div class="absolute right-margin top-space-md z-[1000] flex flex-col gap-space-xs" :class="{ 'pt-safe': expanded }">
          <button
            v-if="expandable"
            type="button"
            :aria-label="expanded ? 'Свернуть карту' : 'Развернуть карту'"
            class="flex h-10 w-10 items-center justify-center rounded-full bg-surface-container-lowest/95 text-on-surface shadow-float backdrop-blur-md transition-transform hover:scale-105"
            @click="expanded ? collapse() : expand()"
          >
            <MsIcon :name="expanded ? 'close' : 'open_in_new'" :size="20" />
          </button>

          <!-- В превью жестов нет, значит и кнопкам масштаба нечего делать:
               нажатие по карте разворачивает её, дальше всё работает как всегда. -->
          <template v-if="!preview">
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
          </template>
          <slot name="controls" />
        </div>

        <!-- Подсказка вместо пустого прямоугольника: иначе непонятно, что карта живая. -->
        <p
          v-if="preview"
          class="pointer-events-none absolute bottom-space-lg left-1/2 z-[1000] -translate-x-1/2 whitespace-nowrap rounded-full bg-surface-container-lowest/90 px-3 py-1 font-label-sm text-label-sm text-on-surface-variant shadow-sm backdrop-blur-md"
        >
          Нажмите, чтобы открыть карту
        </p>

        <slot />
      </div>
    </Teleport>
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
