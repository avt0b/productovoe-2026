<script setup>
import { ref } from 'vue'
import RouteCard from './RouteCard.vue'
import RouteMapModal from './RouteMapModal.vue'

const routes = [
  {
    title: 'Оборона высоты 214',
    location: 'Мценский район, шоссе Орёл — Тула',
    imageUrl: 'https://loremflickr.com/400/300/forest,trail?lock=301',
    distanceKm: 3.2,
    durationMin: 70,
    ageTag: 'Для семьи, 8+',
    questPoints: 4,
    arPoints: 1,
    path: [
      [53.283, 36.56],
      [53.287, 36.568],
      [53.291, 36.58],
    ],
  },
  {
    title: 'Десант над Крупышино',
    location: 'с. Крупышино, Кромской район',
    imageUrl: 'https://loremflickr.com/400/300/countryside,path?lock=302',
    distanceKm: 2.1,
    durationMin: 45,
    ageTag: 'Для семьи, 6+',
    questPoints: 3,
    arPoints: 1,
    path: [
      [52.712, 34.975],
      [52.708, 34.982],
      [52.705, 34.99],
    ],
  },
  {
    title: 'Эскадрилья «Нормандия — Неман»',
    location: 'Орловская область, аэродром подскока',
    imageUrl: 'https://loremflickr.com/400/300/airfield,field?lock=303',
    distanceKm: 4.6,
    durationMin: 95,
    ageTag: 'Для семьи, 10+',
    questPoints: 5,
    arPoints: 2,
    path: [
      [52.95, 36.05],
      [52.958, 36.07],
      [52.965, 36.09],
    ],
  },
  {
    title: 'Рубеж 4-й танковой бригады Катукова',
    location: 'р. Зуша, Мценский рубеж',
    imageUrl: 'https://loremflickr.com/400/300/river,forest?lock=304',
    distanceKm: 3.8,
    durationMin: 80,
    ageTag: 'Для семьи, 8+',
    questPoints: 4,
    arPoints: 0,
    path: [
      [53.27, 36.54],
      [53.28, 36.57],
      [53.29, 36.6],
    ],
  },
]

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
      <span class="font-label-md text-label-md text-on-surface-variant">{{ routes.length }} маршрута рядом</span>
    </div>
    <div class="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-5">
      <RouteCard v-for="route in routes" :key="route.title" v-bind="route" @start="openRoute(route)" />
    </div>

    <RouteMapModal v-model="mapOpen" :route="selectedRoute" />
  </div>
</template>
