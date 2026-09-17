<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

import BareLayout from '@/app/layouts/BareLayout.vue'
import DetailLayout from '@/app/layouts/DetailLayout.vue'
import TabsLayout from '@/app/layouts/TabsLayout.vue'

const route = useRoute()

/** Каркас экрана выбирает сам экран через `meta.layout`; по умолчанию — с вкладками. */
const layouts = { tabs: TabsLayout, detail: DetailLayout, bare: BareLayout }
const layout = computed(() => layouts[route.meta.layout ?? 'tabs'])
</script>

<template>
  <component :is="layout">
    <RouterView />
  </component>
</template>
