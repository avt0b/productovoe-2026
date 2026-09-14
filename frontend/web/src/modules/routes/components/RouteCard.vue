<script setup>
import MobileOnlyBadge from '@shared/components/MobileOnlyBadge.vue'
import SmartImage from '@shared/components/SmartImage.vue'

defineProps({
  imageUrl: { type: String, default: '' },
  title: { type: String, default: '' },
  location: { type: String, default: '' },
  distanceKm: { type: Number, default: 0 },
  durationMin: { type: Number, default: 0 },
  ageTag: { type: String, default: 'Для семьи, 6+' },
  questPoints: { type: Number, default: 0 },
  arPoints: { type: Number, default: 0 },
})

defineEmits(['start'])
</script>

<template>
  <div class="bg-surface-container-lowest rounded-lg overflow-hidden shadow-sm hover:shadow-md transition-all flex flex-col">
    <div class="relative h-40 w-full overflow-hidden bg-surface-container-high">
      <SmartImage :src="imageUrl" icon="route" />
      <span class="absolute top-2 left-2 px-2.5 py-0.5 rounded-full bg-secondary-fixed text-on-secondary-fixed font-label-sm text-label-sm font-bold">
        {{ ageTag }}
      </span>
    </div>
    <div class="p-5 flex flex-col gap-3 flex-1">
      <div class="flex flex-col gap-1">
        <h3 class="font-headline-sm text-headline-sm text-on-surface font-bold leading-snug">{{ title }}</h3>
        <span class="font-body-sm text-body-sm text-on-surface-variant flex items-center gap-1">
          <span class="material-symbols-outlined text-[14px]">pin_drop</span>
          {{ location }}
        </span>
      </div>

      <div class="flex items-center gap-4 font-label-sm text-label-sm text-on-surface-variant">
        <span class="flex items-center gap-1">
          <span class="material-symbols-outlined text-[16px]">hiking</span>
          {{ distanceKm }} км
        </span>
        <span class="flex items-center gap-1">
          <span class="material-symbols-outlined text-[16px]">schedule</span>
          ~{{ durationMin }} мин
        </span>
        <span class="flex items-center gap-1">
          <span class="material-symbols-outlined text-[16px]">stars</span>
          {{ questPoints }} точек
        </span>
      </div>

      <div v-if="arPoints > 0" class="flex items-center gap-2">
        <MobileOnlyBadge :label="`${arPoints} AR-точки`" />
      </div>

      <button
        class="mt-auto w-full py-2.5 rounded-full bg-primary hover:bg-primary/90 text-on-primary font-label-md text-label-md font-bold shadow-sm transition-all flex items-center justify-center gap-2"
        @click="$emit('start')"
      >
        <span class="material-symbols-outlined text-[18px]">route</span>
        <span>Начать маршрут</span>
      </button>
    </div>
  </div>
</template>
