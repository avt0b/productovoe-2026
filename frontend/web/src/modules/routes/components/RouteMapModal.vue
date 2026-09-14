<script setup>
import { ref, watch } from 'vue'
import LeafletMap from '@shared/components/LeafletMap.vue'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  route: { type: Object, default: null },
})
const emit = defineEmits(['update:modelValue'])

const status = ref('building')
const revealedPath = ref([])

watch(
  () => props.modelValue,
  (open) => {
    if (!open) return
    status.value = 'building'
    revealedPath.value = []
    setTimeout(() => {
      status.value = 'ready'
      revealedPath.value = props.route?.path ?? []
    }, 1000)
  },
)

function close() {
  emit('update:modelValue', false)
}
</script>

<template>
  <div
    v-if="modelValue"
    class="fixed inset-0 z-50 bg-on-background/40 backdrop-blur-sm flex items-center justify-center p-4"
    @click.self="close"
  >
    <div class="bg-surface-container-lowest rounded-lg max-w-2xl w-full shadow-2xl flex flex-col overflow-hidden">
      <div class="flex items-center justify-between p-5 border-b border-surface-container-high">
        <div class="flex flex-col">
          <span class="font-headline-sm text-headline-sm text-on-surface font-bold">{{ route?.title }}</span>
          <span class="font-body-sm text-body-sm text-on-surface-variant">{{ route?.location }}</span>
        </div>
        <button
          class="w-8 h-8 rounded-full bg-surface-container hover:bg-surface-container-high text-on-surface flex items-center justify-center transition-colors"
          @click="close"
        >
          <span class="material-symbols-outlined text-[18px]">close</span>
        </button>
      </div>

      <div class="relative h-80 bg-surface-container overflow-hidden">
        <LeafletMap
          v-if="route"
          :center="route.path?.[0] ?? [52.9651, 36.0785]"
          :zoom="13"
          :path="revealedPath"
          :markers="
            status === 'ready' && route.path?.length
              ? [
                  { lat: route.path[0][0], lng: route.path[0][1], title: 'Старт' },
                  { lat: route.path.at(-1)[0], lng: route.path.at(-1)[1], title: 'Финиш' },
                ]
              : []
          "
        />

        <div class="absolute bottom-3 left-3 right-3 flex items-center justify-between pointer-events-none">
          <span class="px-3 py-1.5 rounded-full bg-surface-container-lowest/90 backdrop-blur font-label-sm text-label-sm font-bold text-on-surface flex items-center gap-1.5">
            <span class="material-symbols-outlined text-[16px]" :class="{ 'animate-spin': status === 'building' }">
              {{ status === 'building' ? 'sync' : 'check_circle' }}
            </span>
            {{ status === 'building' ? 'Прокладываем маршрут...' : 'Маршрут построен' }}
          </span>
        </div>
      </div>

      <div class="p-5 flex items-center justify-between gap-3 flex-wrap">
        <div class="flex items-center gap-4 font-label-sm text-label-sm text-on-surface-variant">
          <span class="flex items-center gap-1">
            <span class="material-symbols-outlined text-[16px]">hiking</span>
            {{ route?.distanceKm }} км
          </span>
          <span class="flex items-center gap-1">
            <span class="material-symbols-outlined text-[16px]">schedule</span>
            ~{{ route?.durationMin }} мин
          </span>
        </div>
        <button
          class="px-5 py-2.5 rounded-full bg-primary text-on-primary font-label-md text-label-md font-bold shadow-sm flex items-center gap-2"
          :disabled="status !== 'ready'"
          @click="close"
        >
          <span class="material-symbols-outlined text-[18px]">navigation</span>
          <span>Открыть навигацию в приложении</span>
        </button>
      </div>
    </div>
  </div>
</template>
