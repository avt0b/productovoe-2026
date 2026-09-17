<script setup>
import SmartImage from '@shared/components/SmartImage.vue'

const photos = [
  {
    imageUrl: 'https://loremflickr.com/400/300/map,vintage,document?lock=112',
    placeholderIcon: 'map',
    caption: 'Карта 1941 г.',
    cornerIcon: 'zoom_in',
    tag: 'ЦАМО РФ',
    tagClass: 'bg-on-background/70 text-surface',
  },
  {
    imageUrl: 'https://loremflickr.com/400/300/archaeology,dig?lock=213',
    placeholderIcon: 'terrain',
    caption: 'Полевой сектор',
    cornerIcon: 'photo_camera',
    tag: 'Сектор А-14',
    tagClass: 'bg-secondary text-on-secondary',
  },
]
</script>

<template>
  <div class="grid grid-cols-2 gap-3">
    <div v-for="photo in photos" :key="photo.caption" class="group relative rounded-DEFAULT overflow-hidden bg-surface-container-high aspect-[4/3] shadow-sm">
      <SmartImage
        :src="photo.imageUrl"
        :icon="photo.placeholderIcon"
        img-class="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
      />
      <div class="absolute inset-0 bg-gradient-to-t from-on-background/80 via-on-background/20 to-transparent" />
      <div class="absolute bottom-2 left-2 right-2 flex items-center justify-between text-on-primary">
        <span class="font-label-sm text-label-sm font-bold drop-shadow">{{ photo.caption }}</span>
        <span class="material-symbols-outlined text-[16px]">{{ photo.cornerIcon }}</span>
      </div>
      <span class="absolute top-2 left-2 px-2 py-0.5 rounded-full font-label-sm text-label-sm backdrop-blur" :class="photo.tagClass">
        {{ photo.tag }}
      </span>
    </div>
  </div>
</template>
