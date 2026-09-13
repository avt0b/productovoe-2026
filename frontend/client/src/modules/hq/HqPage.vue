<script setup lang="ts">
import { useAsync } from '@/core/async'
import MsIcon from '@/ui/MsIcon.vue'
import StateBlock from '@/ui/StateBlock.vue'

import CampaignCard from './components/CampaignCard.vue'
import FieldEventCard from './components/FieldEventCard.vue'
import SeasonImpactCard from './components/SeasonImpactCard.vue'
import { fetchHq } from './data'

const { data, loading, error, retry } = useAsync(fetchHq)
</script>

<template>
  <div class="flex w-full flex-col gap-space-lg px-margin pb-6">
    <StateBlock v-if="loading || error" :loading="loading" :error="error" @retry="retry" />

    <template v-else-if="data">
      <SeasonImpactCard :season="data.season" />

      <section class="flex flex-col gap-space-sm">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2">
            <MsIcon name="handshake" :size="22" class="text-primary" />
            <h2 class="font-headline-md text-headline-md text-on-surface">Целевые сборы отрядов</h2>
          </div>
          <button type="button" class="font-label-md text-label-md text-primary transition-opacity hover:opacity-80">
            Все сборы ({{ data.campaignsTotal }})
          </button>
        </div>
        <CampaignCard :campaign="data.campaign" />
      </section>

      <section class="flex flex-col gap-space-sm">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2">
            <MsIcon name="backpack" :size="22" class="text-secondary" />
            <h2 class="font-headline-md text-headline-md text-on-surface">Выходные с поисковиком</h2>
          </div>
          <span class="rounded-full bg-field px-2.5 py-1 font-label-sm text-label-sm text-on-secondary">Полевая школа</span>
        </div>
        <FieldEventCard :event="data.event" />
      </section>
    </template>
  </div>
</template>
