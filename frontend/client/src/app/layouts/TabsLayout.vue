<script setup lang="ts">
import BottomNav from '@/ui/BottomNav.vue'
</script>

<template>
  <div class="relative mx-auto flex min-h-screen w-full max-w-app flex-col bg-surface">
    <!--
      Шапки с названием экрана нет: каждый экран открывается сразу содержимым,
      а где он находится, видно по нижней панели. `pt-safe` держит содержимое
      ниже системной полосы — раньше этот отступ брала на себя шапка.

      pb-28: нижняя панель висит над контентом, последний блок не должен под неё уходить.
    -->
    <main
      class="flex w-full flex-1 flex-col bg-surface pb-28 pt-[calc(env(safe-area-inset-top,0px)+theme(spacing.space-md))]"
    >
      <slot />
    </main>
    <BottomNav />
  </div>
</template>
