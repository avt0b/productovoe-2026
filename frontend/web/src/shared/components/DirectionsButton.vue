<script setup>
import { ref } from 'vue'

const props = defineProps({
  point: { type: Object, required: true },
})

// Своего движка построения маршрутов у нас нет — честный вариант: спросить
// геолокацию браузера и открыть готовый маршрут во внешних картах, а не
// притворяться, что мы сами прокладываем путь.
const status = ref('idle') // idle | locating | error
const error = ref('')

// rtext — точки маршрута через "~" (lat,lon~lat,lon), rtt=auto — на машине.
// Точку отправления можно оставить пустой (rtext=~lat,lon) — Яндекс.Карты
// сами попросят её ввести.
function openDirections(fromLat, fromLon) {
  const url = `https://yandex.ru/maps/?rtext=${fromLat},${fromLon}~${props.point.lat},${props.point.lon}&rtt=auto`
  window.open(url, '_blank', 'noopener')
}

function buildRoute() {
  error.value = ''
  if (!navigator.geolocation) {
    // Геолокации нет (или страница не по HTTPS) — открываем маршрут без
    // точки отправления, внешние карты сами предложат её ввести.
    window.open(`https://yandex.ru/maps/?rtext=~${props.point.lat},${props.point.lon}&rtt=auto`, '_blank', 'noopener')
    return
  }
  status.value = 'locating'
  navigator.geolocation.getCurrentPosition(
    (position) => {
      status.value = 'idle'
      openDirections(position.coords.latitude, position.coords.longitude)
    },
    () => {
      status.value = 'error'
      error.value = 'Не удалось определить ваше местоположение — разрешите доступ к геолокации или введите точку отправления вручную'
    },
    { enableHighAccuracy: true, timeout: 10_000 },
  )
}
</script>

<template>
  <div class="flex flex-col gap-1.5">
    <button
      type="button"
      class="w-full h-11 py-2.5 px-6 rounded-full bg-primary text-on-primary font-label-lg text-label-lg font-bold hover:opacity-95 transition-all flex items-center justify-center gap-2.5 disabled:opacity-60"
      :disabled="status === 'locating'"
      @click="buildRoute"
    >
      <span class="material-symbols-outlined text-[20px]" :class="{ 'animate-spin': status === 'locating' }">
        {{ status === 'locating' ? 'sync' : 'directions' }}
      </span>
      <span>{{ status === 'locating' ? 'Определяем ваше местоположение...' : 'Построить маршрут до точки' }}</span>
    </button>
    <p v-if="error" class="font-label-sm text-label-sm text-error font-bold">{{ error }}</p>
  </div>
</template>
