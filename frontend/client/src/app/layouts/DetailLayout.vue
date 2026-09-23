<script setup lang="ts">
import DetailHeader from '@/ui/DetailHeader.vue'
</script>

<template>
  <div class="relative mx-auto flex min-h-screen w-full max-w-app flex-col bg-surface">
    <DetailHeader />
    <main class="pt-header pb-safe flex w-full flex-1 flex-col bg-surface">
      <slot />
    </main>
  </div>
</template>
