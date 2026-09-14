<script setup>
import { computed, ref, watch } from 'vue'
import LeafletMap from '@shared/components/LeafletMap.vue'
import { useAuthSession } from '@modules/auth'
import * as routesApi from '../api.js'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  route: { type: Object, default: null },
})
const emit = defineEmits(['update:modelValue'])

const { session } = useAuthSession()

const status = ref('building')
const revealedPath = ref([])
const completedIds = ref(new Set())
const progressError = ref('')

const markers = computed(() => {
  if (status.value !== 'ready' || !props.route?.waypoints?.length) return []
  return props.route.waypoints.map((w) => ({
    id: w.id,
    lat: w.lat,
    lng: w.lon,
    title: w.title,
    subtitle: w.kid_task,
  }))
})

watch(
  () => props.modelValue,
  async (open) => {
    if (!open) return
    status.value = 'building'
    revealedPath.value = []
    completedIds.value = new Set()
    progressError.value = ''

    if (session.status === 'authenticated' && props.route) {
      try {
        await routesApi.startProgress(session.accessToken, props.route.id)
        const progress = await routesApi.getMyProgress(session.accessToken, props.route.id)
        completedIds.value = new Set(progress.completed_waypoint_ids)
      } catch {
        // прогресс — необязательная функция витрины, не блокируем показ маршрута
      }
    }

    setTimeout(() => {
      status.value = 'ready'
      revealedPath.value = props.route?.path ?? []
    }, 1000)
  },
)

async function toggleWaypoint(waypointId) {
  if (session.status !== 'authenticated') {
    progressError.value = 'Войдите, чтобы отмечать пройденные точки'
    return
  }
  if (completedIds.value.has(waypointId)) return // отмена пока не поддержана API
  try {
    const progress = await routesApi.completeWaypoint(session.accessToken, props.route.id, waypointId)
    completedIds.value = new Set(progress.completed_waypoint_ids)
  } catch (err) {
    progressError.value = err.detail ?? 'Не удалось отметить точку'
  }
}

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
    <div class="bg-surface-container-lowest rounded-lg max-w-2xl w-full shadow-2xl flex flex-col overflow-hidden max-h-[90vh]">
      <div class="flex items-center justify-between p-5 border-b border-surface-container-high shrink-0">
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

      <div class="relative h-80 bg-surface-container overflow-hidden shrink-0">
        <LeafletMap v-if="route" :center="route.path?.[0] ?? [52.9651, 36.0785]" :zoom="13" :path="revealedPath" :markers="markers" />

        <div class="absolute bottom-3 left-3 right-3 flex items-center justify-between pointer-events-none">
          <span class="px-3 py-1.5 rounded-full bg-surface-container-lowest/90 backdrop-blur font-label-sm text-label-sm font-bold text-on-surface flex items-center gap-1.5">
            <span class="material-symbols-outlined text-[16px]" :class="{ 'animate-spin': status === 'building' }">
              {{ status === 'building' ? 'sync' : 'check_circle' }}
            </span>
            {{ status === 'building' ? 'Прокладываем маршрут...' : 'Маршрут построен' }}
          </span>
        </div>
      </div>

      <div v-if="status === 'ready' && route?.waypoints?.length" class="p-5 flex flex-col gap-2.5 overflow-y-auto border-b border-surface-container-high">
        <span class="font-label-sm text-label-sm text-on-surface-variant uppercase font-bold">Точки маршрута</span>
        <label
          v-for="wp in route.waypoints"
          :key="wp.id"
          class="flex items-start gap-3 p-3 rounded-DEFAULT bg-surface-container-low hover:bg-surface-container cursor-pointer transition-colors"
        >
          <input
            type="checkbox"
            class="w-5 h-5 mt-0.5 rounded accent-primary cursor-pointer"
            :checked="completedIds.has(wp.id)"
            @change="toggleWaypoint(wp.id)"
          />
          <div class="flex flex-col min-w-0">
            <span class="font-label-md text-label-md text-on-surface font-bold">{{ wp.title }}</span>
            <span v-if="wp.story" class="font-body-sm text-body-sm text-on-surface-variant">{{ wp.story }}</span>
            <span v-if="wp.kid_task" class="font-label-sm text-label-sm text-secondary font-bold mt-1">
              Задание: {{ wp.kid_task }}
            </span>
          </div>
        </label>
        <p v-if="progressError" class="font-label-sm text-label-sm text-error font-bold">{{ progressError }}</p>
      </div>

      <div class="p-5 flex items-center justify-between gap-3 flex-wrap shrink-0">
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
