<script setup>
import SmartImage from '@shared/components/SmartImage.vue'

defineProps({
  relics: {
    type: Array,
    default: () => [
      {
        tag: 'Письмо-треугольник',
        title: '«Милая мама, стоим у реки...»',
        meta: 'Полевая почта 114, 12 декабря 1941',
        imageUrl: 'https://loremflickr.com/400/300/letter,handwriting,vintage?lock=105',
      },
      {
        tag: 'Наградной лист',
        title: 'К медали «За отвагу» с печатью',
        meta: 'Штаб 409 СП, 15 января 1942',
        imageUrl: 'https://loremflickr.com/400/300/certificate,document,paper?lock=106',
      },
      {
        tag: 'Личная вещь',
        title: 'Котелок с гравировкой «А.В.»',
        meta: 'Передан поисковым отрядом в 2019 г.',
        imageUrl: 'https://loremflickr.com/400/300/metal,tool?lock=208',
      },
    ],
  },
})
</script>

<template>
  <div class="bg-surface-container-lowest rounded-lg p-6 shadow-sm flex flex-col gap-5">
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-2.5">
        <span class="material-symbols-outlined text-primary text-[22px]">inventory_2</span>
        <span class="font-headline-sm text-headline-sm text-on-surface">Семейные реликвии бойца</span>
      </div>
      <span class="font-label-sm text-label-sm text-secondary font-bold">{{ relics.length }} оцифрованных документа</span>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
      <div
        v-for="relic in relics"
        :key="relic.title"
        class="rounded-DEFAULT bg-surface-container-low overflow-hidden flex flex-col group cursor-pointer hover:shadow-md transition-all"
      >
        <div class="relative h-36 w-full overflow-hidden bg-surface-container-high">
          <SmartImage
            :src="relic.imageUrl"
            icon="description"
            img-class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
          />
          <div class="absolute bottom-2 left-2 px-2 py-0.5 rounded-full bg-black/60 text-white font-label-sm text-label-sm backdrop-blur-sm">
            {{ relic.tag }}
          </div>
        </div>
        <div class="p-3.5 flex flex-col gap-1">
          <span class="font-label-md text-label-md text-on-surface font-bold truncate">{{ relic.title }}</span>
          <span class="font-body-sm text-body-sm text-on-surface-variant">{{ relic.meta }}</span>
        </div>
      </div>
    </div>
  </div>
</template>
