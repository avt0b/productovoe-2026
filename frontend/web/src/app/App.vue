<script setup>
import { useRoute } from 'vue-router'
import AppSidebar from './components/AppSidebar.vue'
import AppHeader from './components/AppHeader.vue'
import { useSidebar } from './composables/useSidebar.js'

const route = useRoute()
const { isOpen, toggle, close, closeOnMobile } = useSidebar()
</script>

<template>
  <template v-if="route.meta.standalone">
    <RouterView />
  </template>
  <template v-else>
    <div
      v-if="isOpen"
      class="fixed inset-0 bg-on-background/40 z-40 lg:hidden"
      @click="close"
    />
    <AppSidebar :open="isOpen" @navigate="closeOnMobile" @close="close" />
    <div class="transition-[padding] duration-300 ease-out" :class="isOpen ? 'lg:pl-72' : 'lg:pl-0'">
      <AppHeader :sidebar-open="isOpen" @toggle-sidebar="toggle" />
      <main class="relative pt-16 w-full px-4 sm:px-6 lg:px-8 bg-surface min-h-screen">
        <RouterView />
      </main>
    </div>
  </template>
</template>
