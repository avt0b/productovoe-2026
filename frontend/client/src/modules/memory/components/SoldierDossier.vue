<script setup lang="ts">
import MsIcon from '@/ui/MsIcon.vue'

import type { HeroPortrait } from '../data'

defineProps<{ hero: HeroPortrait }>()
</script>

<template>
  <div class="flex flex-col space-y-3 rounded-lg bg-surface-container-lowest p-4 shadow-sm">
    <div class="flex items-start justify-between gap-2">
      <div class="flex flex-col">
        <span class="font-label-sm text-label-sm uppercase tracking-wider text-outline">Архивная карточка</span>
        <h3 class="mt-0.5 font-headline-sm text-headline-sm font-bold leading-tight text-on-surface">{{ hero.name }}</h3>
        <span class="mt-0.5 font-label-md text-label-md font-bold text-primary">{{ hero.years }}</span>
      </div>
      <div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-primary-fixed text-primary">
        <MsIcon name="military_tech" :size="22" filled />
      </div>
    </div>

    <dl class="flex flex-col space-y-2 pt-1">
      <div class="flex items-center gap-2.5 text-on-surface">
        <div class="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-surface-container text-secondary">
          <MsIcon name="groups" :size="16" />
        </div>
        <div class="flex min-w-0 flex-col">
          <dt class="font-label-sm text-label-sm text-outline">Воинское подразделение</dt>
          <dd class="truncate font-body-sm text-body-sm font-semibold">{{ hero.unit }}</dd>
        </div>
      </div>
      <div class="flex items-center gap-2.5 text-on-surface">
        <div class="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-surface-container text-secondary">
          <MsIcon name="home_pin" :size="16" />
        </div>
        <div class="flex min-w-0 flex-col">
          <dt class="font-label-sm text-label-sm text-outline">Место призыва и родина</dt>
          <dd class="truncate font-body-sm text-body-sm font-semibold">{{ hero.homeland }}</dd>
        </div>
      </div>
    </dl>
  </div>
</template>
