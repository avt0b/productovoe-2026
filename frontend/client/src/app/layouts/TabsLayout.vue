<script setup lang="ts">
import AppHeader from '@/ui/AppHeader.vue'
import BottomNav from '@/ui/BottomNav.vue'
</script>

<template>
  <div class="relative mx-auto flex min-h-screen w-full max-w-app flex-col bg-surface">
    <AppHeader />
    <!-- Шапка и панель вкладок висят поверх контента: их высоту (вместе с системными полосами) отступаем. -->
    <main class="pt-header pb-nav flex w-full flex-1 flex-col bg-surface">
      <slot />
    </main>
    <BottomNav />
  </div>
</template>
