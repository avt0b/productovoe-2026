<script setup>
import MobileOnlyBadge from '@shared/components/MobileOnlyBadge.vue'

const points = [
  { icon: 'star', label: 'Бой', text: 'Место сражения — карточка с историей и заданием' },
  { icon: 'sports_motorsports', label: 'Окоп', text: '«Найди окоп» — точка дополненной реальности', mobileOnly: true },
  { icon: 'menu_book', label: 'Штаб', text: 'Архивная справка и аудиофрагмент воспоминаний' },
]
</script>

<template>
  <div class="bg-surface-container-lowest rounded-DEFAULT p-5 shadow-sm flex flex-col gap-4">
    <span class="font-label-lg text-label-lg text-on-surface font-bold">Как читать метки на маршруте</span>
    <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
      <div v-for="point in points" :key="point.label" class="flex items-start gap-3">
        <div class="w-9 h-9 rounded-full bg-secondary-container text-on-secondary-container flex items-center justify-center shrink-0">
          <span class="material-symbols-outlined text-[18px]">{{ point.icon }}</span>
        </div>
        <div class="flex flex-col gap-1">
          <div class="flex items-center gap-2 flex-wrap">
            <span class="font-label-md text-label-md text-on-surface font-bold">{{ point.label }}</span>
            <MobileOnlyBadge v-if="point.mobileOnly" />
          </div>
          <span class="font-body-sm text-body-sm text-on-surface-variant">{{ point.text }}</span>
        </div>
      </div>
    </div>
  </div>
</template>
