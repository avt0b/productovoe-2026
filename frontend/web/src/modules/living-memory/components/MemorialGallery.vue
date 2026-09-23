<script setup>
import { onMounted, ref } from 'vue'
import * as api from '../api.js'

const clips = ref([])
const status = ref('loading') // loading | loaded | error

onMounted(async () => {
  try {
    clips.value = await api.listPublicClips()
    status.value = 'loaded'
  } catch {
    status.value = 'error'
  }
})
</script>

<template>
  <div class="bg-surface-container-lowest rounded-lg p-6 shadow-sm flex flex-col gap-4">
    <div class="flex items-center gap-2.5">
      <span class="material-symbols-outlined text-primary text-[22px]">auto_awesome</span>
      <div class="flex flex-col">
        <span class="font-headline-sm text-headline-sm text-on-surface">Общий мемориал</span>
        <span class="font-body-sm text-body-sm text-on-surface-variant">
          Готовые «живые фото», которые авторы решили показать всем — media_service, GET /clips
        </span>
      </div>
    </div>

    <p v-if="status === 'error'" class="font-body-sm text-body-sm text-error">
      Не удалось загрузить общий мемориал — media_service недоступен
    </p>
    <p v-else-if="status === 'loaded' && !clips.length" class="font-body-sm text-body-sm text-on-surface-variant">
      Здесь появятся готовые ролики, как только кто-то отметит своё «живое фото» видимым для всех —
      пока в этом окружении нет воркера, который бы их дорендерил
    </p>

    <div v-else-if="clips.length" class="grid grid-cols-1 sm:grid-cols-2 gap-3">
      <div
        v-for="clip in clips"
        :key="clip.id"
        class="bg-surface-container-low rounded-DEFAULT p-3.5 flex flex-col gap-2"
      >
        <video v-if="clip.video_url" :src="clip.video_url" class="w-full aspect-video rounded-[6px] bg-surface-container-high" controls />
        <span class="font-label-md text-label-md text-on-surface font-bold">{{ clip.soldier_name || 'Неизвестный боец' }}</span>
        <p v-if="clip.narration_text" class="font-body-sm text-body-sm text-on-surface-variant line-clamp-3">
          {{ clip.narration_text }}
        </p>
      </div>
    </div>
  </div>
</template>
