<script setup>
const guides = [
  { name: 'Михаил Смирнов', role: 'Командир отряда «Высота» • Стаж 18 лет', rating: 4.9, tours: 62 },
  { name: 'Анна Ковалёва', role: 'Краевед, музей г. Мценска • Стаж 9 лет', rating: 4.8, tours: 41 },
  { name: 'Егор Лисицын', role: 'Отряд «Рубеж» • Стаж 6 лет', rating: 4.6, tours: 23 },
]
</script>

<template>
  <div class="flex flex-col gap-2.5">
    <div
      v-for="guide in guides"
      :key="guide.name"
      class="bg-surface-container-low p-3.5 rounded-DEFAULT flex items-center justify-between gap-3"
    >
      <div class="flex flex-col min-w-0">
        <span class="font-label-md text-label-md text-on-surface font-bold truncate">{{ guide.name }}</span>
        <span class="font-body-sm text-body-sm text-on-surface-variant">{{ guide.role }}</span>
      </div>
      <div class="flex flex-col items-end gap-0.5 shrink-0">
        <span class="flex items-center gap-1 font-label-md text-label-md font-bold text-tertiary">
          <span class="material-symbols-outlined text-[16px]" style="font-variation-settings: 'FILL' 1">star</span>
          {{ guide.rating }}
        </span>
        <span class="font-label-sm text-label-sm text-on-surface-variant">{{ guide.tours }} экскурсий</span>
      </div>
    </div>
  </div>
</template>
