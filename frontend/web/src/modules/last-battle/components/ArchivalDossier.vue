<script setup>
import DossierHeader from './DossierHeader.vue'
import ComparativePhotos from './ComparativePhotos.vue'
import ArchivalMetadata from './ArchivalMetadata.vue'
import ExpeditionActivity from './ExpeditionActivity.vue'
import DossierActions from './DossierActions.vue'

defineEmits(['open-upload'])
</script>

<template>
  <div class="bg-surface-container-lowest rounded-lg p-6 shadow-md flex flex-col gap-5">
    <DossierHeader />
    <ComparativePhotos />
    <ArchivalMetadata />
    <ExpeditionActivity />
    <DossierActions @open-upload="$emit('open-upload')" />
  </div>
</template>
