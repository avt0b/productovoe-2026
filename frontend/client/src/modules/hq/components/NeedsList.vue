<script setup lang="ts">
import MsIcon from '@/ui/MsIcon.vue'

import { NEED_KINDS, type Need, type Squad } from '../data'

/** «Карта потребностей» без денег: нужны люди, нужно снаряжение. */
defineProps<{
  needs: Need[]
  squads: Map<string, Squad>
}>()
</script>

<template>
  <ul class="flex flex-col gap-space-sm">
    <li v-for="need in needs" :key="need.id" class="flex items-start gap-space-sm rounded-DEFAULT bg-surface-container-lowest p-space-md shadow-sm">
      <div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-tertiary-fixed text-on-tertiary-fixed">
        <MsIcon :name="NEED_KINDS[need.kind].icon" :size="20" />
      </div>
      <div class="min-w-0 flex-1">
        <div class="flex items-center justify-between gap-2">
          <span class="font-label-sm text-label-sm uppercase tracking-wider text-outline">{{ NEED_KINDS[need.kind].title }}</span>
          <span class="truncate font-label-sm text-label-sm text-on-surface-variant">{{ squads.get(need.squad_id)?.region }}</span>
        </div>
        <h4 class="font-label-lg text-label-lg text-on-surface">{{ need.title }}</h4>
        <p class="font-body-sm text-body-sm text-on-surface-variant">{{ squads.get(need.squad_id)?.name }}</p>
        <p v-if="need.description" class="mt-1 font-body-sm text-body-sm text-on-surface-variant">{{ need.description }}</p>
      </div>
    </li>
  </ul>
</template>
