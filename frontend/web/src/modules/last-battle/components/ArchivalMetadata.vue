<script setup>
import { computed } from 'vue'

const props = defineProps({
  point: { type: Object, default: null },
})

const STATUS_LABEL = {
  discovered: 'Обнаружено, требуется проверка',
  archive_confirmed: 'Подтверждено архивом',
  remains_raised: 'Останки подняты',
}

function formatCoords(lat, lon) {
  const fmt = (value, pos, neg) => {
    const abs = Math.abs(value)
    const deg = Math.floor(abs)
    const min = Math.floor((abs - deg) * 60)
    const sec = Math.round(((abs - deg) * 60 - min) * 60)
    return `${deg}°${min}'${sec}" ${value >= 0 ? pos : neg}`
  }
  return `${fmt(lat, 'N', 'S')}, ${fmt(lon, 'E', 'W')}`
}

const coordsText = computed(() => (props.point ? formatCoords(props.point.lat, props.point.lon) : ''))
const statusLabel = computed(() => STATUS_LABEL[props.point?.status] ?? '')
</script>

<template>
  <div v-if="point" class="flex flex-col gap-2.5">
    <div class="bg-surface-container-low p-3.5 rounded-DEFAULT flex items-start gap-3">
      <span class="material-symbols-outlined text-primary text-[22px] shrink-0 mt-0.5">location_on</span>
      <div class="flex flex-col min-w-0">
        <span class="font-label-sm text-label-sm text-on-surface-variant font-bold uppercase tracking-wider">Точные полевые координаты</span>
        <span class="font-body-md text-body-md text-on-surface font-semibold truncate">{{ coordsText }}</span>
        <span v-if="point.unit" class="font-body-sm text-body-sm text-on-surface-variant">{{ point.unit }}</span>
      </div>
    </div>

    <div v-if="point.source" class="bg-surface-container-low p-3.5 rounded-DEFAULT flex items-start gap-3">
      <span class="material-symbols-outlined text-tertiary text-[22px] shrink-0 mt-0.5">menu_book</span>
      <div class="flex flex-col min-w-0">
        <span class="font-label-sm text-label-sm text-on-surface-variant font-bold uppercase tracking-wider">Архивный источник</span>
        <span class="font-body-md text-body-md text-on-surface font-semibold">{{ point.source }}</span>
      </div>
    </div>

    <div class="bg-surface-container p-3.5 rounded-DEFAULT flex items-start gap-3">
      <span class="material-symbols-outlined text-primary text-[22px] shrink-0 mt-0.5">fingerprint</span>
      <div class="flex flex-col min-w-0">
        <div class="flex items-center gap-2">
          <span class="font-label-sm text-label-sm text-primary font-bold uppercase tracking-wider">Статус</span>
          <span class="px-2 py-0.2 rounded-full bg-primary-fixed text-on-primary-fixed font-label-sm text-label-sm font-bold">
            {{ statusLabel }}
          </span>
        </div>
        <p v-if="point.circumstances" class="font-body-sm text-body-sm text-on-surface-variant mt-0.5">
          {{ point.circumstances }}
        </p>
      </div>
    </div>
  </div>
  <p v-else class="font-body-md text-body-md text-on-surface-variant">Выберите точку на карте, чтобы увидеть досье.</p>
</template>
