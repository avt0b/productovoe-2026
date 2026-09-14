<script setup>
import { ref } from 'vue'
import PriorityAlert from './components/PriorityAlert.vue'
import StatusFilters from './components/StatusFilters.vue'
import TacticalMap from './components/TacticalMap.vue'
import TacticalMetrics from './components/TacticalMetrics.vue'
import ArchivalDossier from './components/ArchivalDossier.vue'
import ContributionModal from './components/ContributionModal.vue'

const uploadModalOpen = ref(false)
</script>

<template>
  <div class="flex flex-col w-full pb-16">
    <PriorityAlert />
    <StatusFilters />

    <section class="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
      <div class="lg:col-span-7 flex flex-col gap-4">
        <TacticalMap />
        <TacticalMetrics />
      </div>

      <div class="lg:col-span-5 flex flex-col gap-5">
        <ArchivalDossier @open-upload="uploadModalOpen = true" />
      </div>
    </section>

    <ContributionModal v-model="uploadModalOpen" />
  </div>
</template>
