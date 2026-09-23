<script setup>
import { ref, watch } from 'vue'
import * as fundraisingApi from '../api.js'

// guides: [{ id: guideId, label }] — собирается вызывающим компонентом из
// списка загруженных экскурсий (search_hq_service не отдаёт отдельный
// список «гидов», только guide_id на каждой экскурсии).
const props = defineProps({
  guides: { type: Array, default: () => [] },
})

const summaries = ref({})

async function loadFor(guide) {
  if (summaries.value[guide.id] !== undefined) return
  try {
    const summary = await fundraisingApi.getGuideRating(guide.id)
    summaries.value = { ...summaries.value, [guide.id]: summary }
  } catch {
    summaries.value = { ...summaries.value, [guide.id]: null }
  }
}

watch(
  () => props.guides,
  (list) => list.forEach(loadFor),
  { immediate: true },
)
</script>

<template>
  <div class="flex flex-col gap-2.5">
    <p v-if="!guides.length" class="font-body-sm text-body-sm text-on-surface-variant">
      Пока нет запланированных экскурсий с гидом — рейтинг из guides.py появится, когда штаб заведёт первую
    </p>
    <div
      v-for="guide in guides"
      :key="guide.id"
      class="bg-surface-container-low p-3.5 rounded-DEFAULT flex items-center justify-between gap-3"
    >
      <div class="flex flex-col min-w-0">
        <span class="font-label-md text-label-md text-on-surface font-bold truncate">{{ guide.label }}</span>
        <span class="font-body-sm text-body-sm text-on-surface-variant">Гид search_hq_service</span>
      </div>
      <div class="flex flex-col items-end gap-0.5 shrink-0">
        <template v-if="summaries[guide.id]?.count">
          <span class="flex items-center gap-1 font-label-md text-label-md font-bold text-tertiary">
            <span class="material-symbols-outlined text-[16px]" style="font-variation-settings: 'FILL' 1">star</span>
            {{ summaries[guide.id].average.toFixed(1) }}
          </span>
          <span class="font-label-sm text-label-sm text-on-surface-variant">{{ summaries[guide.id].count }} оценок</span>
        </template>
        <span v-else class="font-label-sm text-label-sm text-on-surface-variant">Пока нет оценок</span>
      </div>
    </div>
  </div>
</template>
