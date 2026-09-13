<script setup lang="ts">
import MsIcon from '@/ui/MsIcon.vue'
</script>

<template>
  <div class="relative w-full overflow-hidden rounded-2xl bg-secondary p-space-md text-on-secondary shadow-md">
    <!-- Топографические горизонтали на фоне -->
    <svg
      class="pointer-events-none absolute inset-0 h-full w-full stroke-current opacity-10"
      fill="none"
      viewBox="0 0 360 140"
      aria-hidden="true"
    >
      <path d="M-20 30 C 40 10, 100 70, 180 40 C 260 10, 320 60, 380 30" stroke-dasharray="4 2" stroke-width="1.5" />
      <path d="M-20 70 C 60 40, 120 110, 200 80 C 280 50, 320 100, 380 70" stroke-width="1.5" />
      <path d="M-20 110 C 50 80, 130 130, 210 100 C 290 70, 330 120, 380 110" stroke-dasharray="3 3" stroke-width="1.5" />
      <circle cx="280" cy="45" r="18" stroke-width="1" />
      <circle cx="280" cy="45" r="6" fill="currentColor" />
    </svg>

    <div class="relative z-10 flex items-start space-x-space-sm">
      <div class="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-secondary-fixed text-on-secondary-fixed">
        <MsIcon name="auto_stories" :size="18" filled />
      </div>
      <div class="flex flex-col">
        <span class="font-label-sm text-label-sm uppercase tracking-wider opacity-80">Экспедиция памяти</span>
        <span class="mt-0.5 font-headline-sm text-headline-sm leading-snug text-on-secondary">
          Сохраняем память поколений вместе
        </span>
        <p class="mt-1 font-body-sm text-body-sm text-secondary-fixed-dim opacity-90">
          Интерактивные исторические карты, архивные свидетельства и архивы семейных подвигов.
        </p>
      </div>
    </div>
  </div>
</template>
