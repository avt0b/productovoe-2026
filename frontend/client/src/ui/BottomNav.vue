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
      <!--
        Активная вкладка раскрывается в таблетку с подписью, остальные остаются
        иконками. Разделов шесть, и на узком экране шесть подписей в строку не
        помещаются: «Маршруты» одним словом не переносится и налезает на
        соседнюю вкладку. Таблетка решает это и заодно говорит, где человек
        находится, тем же приёмом, что переключатель на экране входа. Подпись
        скрытых вкладок остаётся в `aria-label` — скринридер их читает.
      -->
      <nav
        class="pointer-events-auto flex h-16 w-full items-center gap-0.5 rounded-sheet bg-surface-container-lowest/95 px-space-xs shadow-nav backdrop-blur-xl"
      >
        <RouterLink
          v-for="tab in tabs"
          :key="tab.route"
          :to="{ name: tab.route }"
          class="group flex h-11 min-w-0 items-center justify-center gap-1 rounded-full px-1.5 transition-[flex-grow,background-color,color] duration-300 ease-out"
          :class="isActive(tab) ? 'flex-[5] bg-primary-fixed text-primary' : 'flex-1 text-on-surface-variant hover:bg-surface-container'"
          :aria-label="tab.title"
          :aria-current="isActive(tab) ? 'page' : undefined"
        >
          <MsIcon :name="tab.icon" :size="22" :filled="isActive(tab)" class="shrink-0" />
          <span v-if="isActive(tab)" class="truncate font-label-sm text-label-sm">{{ tab.title }}</span>
        </RouterLink>
      </nav>
    </div>
  </div>
</template>
