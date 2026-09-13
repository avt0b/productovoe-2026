<script setup lang="ts">
import { useAsync } from '@/core/async'
import MsIcon from '@/ui/MsIcon.vue'
import StateBlock from '@/ui/StateBlock.vue'

import LivingPortraitPlayer from './components/LivingPortraitPlayer.vue'
import MemoryActions from './components/MemoryActions.vue'
import SoldierDossier from './components/SoldierDossier.vue'
import { fetchPortrait } from './data'

const { data, loading, error, retry } = useAsync(fetchPortrait)
</script>

<template>
  <div class="flex w-full flex-col space-y-space-md px-margin pb-8">
    <div class="flex flex-col space-y-space-xs pt-space-xs">
      <div
        class="inline-flex items-center gap-1.5 self-start rounded-full bg-secondary-container/60 px-3 py-1 text-on-secondary-container"
      >
        <MsIcon name="auto_awesome" :size="16" filled />
        <span class="font-label-sm text-label-sm tracking-wide">Память поколений</span>
      </div>
      <h2 class="font-headline-lg-mobile text-headline-lg-mobile text-on-surface">Оживший портрет героя</h2>
      <p class="font-body-md text-body-md text-outline">Семейный архив и нейросетевая реконструкция</p>
    </div>

    <!-- Этическая пометка: без неё реконструкцию легко принять за подлинную запись. -->
    <div class="flex items-start gap-3 rounded-lg bg-secondary-container/40 p-3.5 shadow-sm">
      <div class="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-secondary-container text-secondary">
        <MsIcon name="shield_with_heart" :size="18" filled />
      </div>
      <p class="font-body-sm text-body-sm leading-snug text-on-secondary-container">
        Технология создана исключительно в мемориальных целях с глубоким уважением к памяти защитников Отечества и
        их семей. Движение и голос — реконструкция по архивной фотографии.
      </p>
    </div>

    <StateBlock v-if="loading || error" :loading="loading" :error="error" @retry="retry" />

    <template v-else-if="data">
      <LivingPortraitPlayer :image="data.hero.portraitImage" :line="data.hero.reconstructedLine" />
      <SoldierDossier :hero="data.hero" />
      <MemoryActions :hero-name="data.hero.name" :line="data.hero.reconstructedLine" :folder="data.archiveFolder" :map-hint="data.mapHint" />
    </template>
  </div>
</template>
