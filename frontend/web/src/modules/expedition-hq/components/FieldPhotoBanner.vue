<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  imageUrl: { type: String, default: 'https://loremflickr.com/1200/450/forest,excavation,expedition?lock=108' },
  eyebrow: { type: String, default: 'Фотохроника раскопа' },
  title: { type: String, default: 'Высота 203.4: Работа в траншеях 11-й Гвардейской армии' },
  photoCount: { type: String, default: '18 кадров' },
})

const loaded = ref(false)

watch(
  () => props.imageUrl,
  (url) => {
    loaded.value = false
    if (!url) return
    const img = new Image()
    img.onload = () => {
      loaded.value = true
    }
    img.src = url
  },
  { immediate: true },
)
</script>

<template>
  <div class="w-full relative rounded-lg overflow-hidden bg-surface-container-high shadow-sm">
    <div
      class="w-full h-56 bg-cover bg-center flex items-end p-6 relative"
      :style="loaded ? { backgroundImage: `url('${imageUrl}')` } : {}"
    >
      <div class="absolute inset-0 bg-gradient-to-t from-on-background/85 via-on-background/30 to-transparent" />
      <span
        v-if="!loaded"
        class="material-symbols-outlined absolute inset-0 flex items-center justify-center text-on-surface-variant text-[48px]"
      >
        photo_camera
      </span>

      <div class="relative z-10 flex flex-col sm:flex-row items-start sm:items-end justify-between w-full gap-4">
        <div>
          <span class="font-label-sm text-label-sm text-secondary-fixed uppercase tracking-wider font-bold">{{ eyebrow }}</span>
          <h3 class="font-headline-md text-headline-md text-on-primary font-bold">{{ title }}</h3>
        </div>
        <span
          class="px-3 py-1.5 rounded-full bg-surface-container-lowest/20 backdrop-blur-md text-on-primary font-label-sm text-label-sm flex items-center gap-1.5"
        >
          <span class="material-symbols-outlined text-[16px]">photo_camera</span>
          {{ photoCount }}
        </span>
      </div>
    </div>
  </div>
</template>
