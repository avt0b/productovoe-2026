<script setup>
import { onMounted, ref } from 'vue'
import RouteCard from './RouteCard.vue'
import RouteMapModal from './RouteMapModal.vue'
import * as routesApi from '../api.js'

const routes = ref([])
const loadStatus = ref('idle') // idle | loading | loaded | error

// Бэкенд не хранит фото обложки для демо-маршрутов (cover_url пуст),
// картинки остаются тематическими заглушками — как и раньше.
const FALLBACK_IMAGES = [
  'https://loremflickr.com/400/300/forest,trail?lock=301',
  'https://loremflickr.com/400/300/countryside,path?lock=302',
  'https://loremflickr.com/400/300/airfield,field?lock=303',
  'https://loremflickr.com/400/300/river,forest?lock=304',
]

async function load() {
  loadStatus.value = 'loading'
  try {
    const list = await routesApi.listRoutes()
    const details = await Promise.all(list.map((r) => routesApi.getRouteDetail(r.id)))
    routes.value = details.map((route, i) => {
      const waypoints = [...route.waypoints].sort((a, b) => a.order_index - b.order_index)
      return {
        id: route.id,
        title: route.title,
        location: route.city,
        imageUrl: route.cover_url || FALLBACK_IMAGES[i % FALLBACK_IMAGES.length],
        distanceKm: route.distance_km,
        // Бэкенд не хранит расчётное время — прикидываем по
        // семейному темпу ~18 мин/км, честно помечено «~» на карточке.
        durationMin: Math.round(route.distance_km * 18),
        ageTag: route.mode === 'family' ? 'Для семьи' : 'Общий маршрут',
        questPoints: waypoints.length,
        arPoints: waypoints.filter((w) => w.ar_hint).length,
        path: waypoints.map((w) => [w.lat, w.lon]),
        waypoints,
      }
    })
    loadStatus.value = 'loaded'
  } catch {
    loadStatus.value = 'error'
  }
}

onMounted(load)

const mapOpen = ref(false)
const selectedRoute = ref(null)

function openRoute(route) {
  selectedRoute.value = route
  mapOpen.value = true
}
</script>

<template>
  <div class="flex flex-col gap-4">
    <div class="flex items-center justify-between">
      <h2 class="font-headline-lg text-headline-lg text-on-surface font-bold">Доступные маршруты</h2>
      <span class="font-label-md text-label-md text-on-surface-variant">
        {{ routes.length }} {{ routes.length === 1 ? 'маршрут' : 'маршрута' }}
      </span>
    </div>

    <p
      v-if="loadStatus === 'loaded' && !routes.length"
      class="bg-surface-container-lowest rounded-lg p-6 text-on-surface-variant font-body-md text-body-md"
    >
      Опубликованных маршрутов пока нет.
    </p>

    <div v-else class="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-5">
      <RouteCard v-for="route in routes" :key="route.id" v-bind="route" @start="openRoute(route)" />
    </div>

    <RouteMapModal v-model="mapOpen" :route="selectedRoute" />
  </div>
</template>
