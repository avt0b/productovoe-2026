<script setup lang="ts">
import AppHeader from '@/ui/AppHeader.vue'
import BottomNav from '@/ui/BottomNav.vue'
</script>

<template>
  <div class="relative mx-auto flex min-h-screen w-full max-w-app flex-col bg-surface">
    <AppHeader />
    <!-- pb-28: нижняя панель висит над контентом, последний блок не должен под неё уходить. -->
    <main class="flex w-full flex-1 flex-col bg-surface pb-28 pt-16">
      <slot />
    </main>
    <BottomNav />
  </div>
</template>
