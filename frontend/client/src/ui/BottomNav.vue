<script setup lang="ts">
import { useRoute } from 'vue-router'

import { tabs } from '@/app/registry'
import type { ModuleTab } from '@/core/module'

import MsIcon from './MsIcon.vue'

const route = useRoute()

/** Вкладка активна на своём экране и на экранах, которые явно к ней привязаны через `meta.tab`. */
function isActive(tab: ModuleTab): boolean {
  return (route.meta.tab ?? route.name) === tab.route
}
</script>

<template>
  <div
    v-if="tabs.length"
    class="pb-safe pointer-events-none fixed inset-x-0 bottom-0 z-50 mx-auto w-full max-w-app"
  >
    <div class="w-full px-margin pb-5">
      <nav
        class="pointer-events-auto flex h-16 w-full items-center justify-around rounded-sheet bg-surface-container-lowest/95 px-space-xs shadow-nav backdrop-blur-xl"
      >
        <RouterLink
          v-for="tab in tabs"
          :key="tab.route"
          :to="{ name: tab.route }"
          class="group flex min-h-11 min-w-14 flex-1 flex-col items-center justify-center py-1 transition-colors"
          :class="isActive(tab) ? 'font-bold text-primary' : 'text-on-surface-variant'"
          :aria-current="isActive(tab) ? 'page' : undefined"
        >
          <MsIcon :name="tab.icon" :size="22" class="transition-transform group-hover:scale-105" />
          <span class="mt-0.5 text-center font-label-sm text-label-sm leading-tight">{{ tab.title }}</span>
        </RouterLink>
      </nav>
    </div>
  </div>
</template>
