<script setup>
import { onMounted, onUnmounted, ref, watch } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import markerIcon2x from 'leaflet/dist/images/marker-icon-2x.png'
import markerIcon from 'leaflet/dist/images/marker-icon.png'
import markerShadow from 'leaflet/dist/images/marker-shadow.png'

delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: markerIcon2x,
  iconUrl: markerIcon,
  shadowUrl: markerShadow,
})

const props = defineProps({
  center: { type: Array, default: () => [52.9651, 36.0785] },
  zoom: { type: Number, default: 13 },
  markers: { type: Array, default: () => [] },
  path: { type: Array, default: () => [] },
  pathColor: { type: String, default: '#ab2e22' },
  scrollWheelZoom: { type: Boolean, default: false },
  fitToMarkers: { type: Boolean, default: true },
})
const emit = defineEmits(['marker-click'])

const mapEl = ref(null)
let map = null
let markerLayer = null
let pathLayer = null

function render() {
  if (!map) return

  markerLayer.clearLayers()
  props.markers.forEach((m) => {
    // m.icon — необязательный: имя Material Symbol + цветовые классы Tailwind
    // (badgeClass/tailClass) рисуют цветную метку-«пин» вместо стандартной
    // капли Leaflet. Без m.icon поведение не меняется — обычный маркер.
    const options = m.icon
      ? {
          icon: L.divIcon({
            className: '',
            html: `<div class="flex flex-col items-center drop-shadow-md">
              <div class="w-8 h-8 rounded-full ${m.badgeClass ?? 'bg-primary'} ring-2 ring-surface-container-lowest flex items-center justify-center">
                <span class="material-symbols-outlined text-white text-[16px]" style="font-variation-settings: 'FILL' 1">${m.icon}</span>
              </div>
              <div class="w-0 h-0 border-x-[5px] border-x-transparent border-t-[7px] ${m.tailClass ?? 'border-t-primary'} -mt-px"></div>
            </div>`,
            iconSize: [32, 40],
            iconAnchor: [16, 40],
            popupAnchor: [0, -36],
          }),
        }
      : {}
    const marker = L.marker([m.lat, m.lng], options).addTo(markerLayer)
    if (m.title) {
      marker.bindPopup(`<b>${m.title}</b>${m.subtitle ? `<br>${m.subtitle}` : ''}`)
    }
    if (m.id !== undefined) {
      marker.on('click', () => emit('marker-click', m.id))
    }
  })

  if (pathLayer) {
    pathLayer.remove()
    pathLayer = null
  }
  if (props.path.length > 1) {
    pathLayer = L.polyline(props.path, { color: props.pathColor, weight: 4, opacity: 0.9 }).addTo(map)
    map.fitBounds(pathLayer.getBounds(), { padding: [32, 32] })
  } else if (props.markers.length && props.fitToMarkers) {
    const bounds = L.latLngBounds(props.markers.map((m) => [m.lat, m.lng]))
    map.fitBounds(bounds, { padding: [48, 48], maxZoom: props.zoom })
  }
}

onMounted(() => {
  map = L.map(mapEl.value, {
    center: props.center,
    zoom: props.zoom,
    zoomControl: false,
    scrollWheelZoom: props.scrollWheelZoom,
  })
  L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors',
    maxZoom: 19,
  }).addTo(map)
  markerLayer = L.layerGroup().addTo(map)
  render()
})

watch(() => [props.markers, props.path], render, { deep: true })

onUnmounted(() => {
  map?.remove()
  map = null
})

defineExpose({
  zoomIn: () => map?.zoomIn(),
  zoomOut: () => map?.zoomOut(),
  invalidateSize: () => map?.invalidateSize(),
})
</script>

<template>
  <div ref="mapEl" class="w-full h-full" />
</template>
