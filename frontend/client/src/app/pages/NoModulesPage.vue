<script setup lang="ts">
import Mascot from '@/ui/Mascot.vue'
import MsIcon from '@/ui/MsIcon.vue'
</script>

<template>
  <div class="flex flex-1 flex-col items-center justify-center gap-space-md px-margin py-space-xl text-center">
    <Mascot pose="question" :size="180" />
    <h1 class="font-headline-lg-mobile text-headline-lg-mobile text-on-surface">Маршруты победы</h1>
    <div class="flex w-full flex-col items-center gap-space-sm rounded-lg bg-surface-container-low p-space-lg">
      <MsIcon name="extension" :size="28" class="text-secondary" />
      <p class="font-body-md text-body-md text-on-surface">Ни одного окна не подключено</p>
      <p class="font-body-sm text-body-sm text-on-surface-variant">
        Окно — это папка <code class="font-label-md">src/modules/&lt;имя&gt;/</code> с файлом
        <code class="font-label-md">index.ts</code>. Приложение найдёт её само.
      </p>
    </div>
  </div>
</template>
