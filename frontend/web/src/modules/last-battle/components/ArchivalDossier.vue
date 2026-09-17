<script setup>
import DossierHeader from './DossierHeader.vue'
import ComparativePhotos from './ComparativePhotos.vue'
import ArchivalMetadata from './ArchivalMetadata.vue'
import ExpeditionActivity from './ExpeditionActivity.vue'
import DossierActions from './DossierActions.vue'

defineProps({
  point: { type: Object, default: null },
})
defineEmits(['open-upload'])
</script>

<template>
  <div class="bg-surface-container-lowest rounded-lg p-6 shadow-md flex flex-col gap-5">
    <DossierHeader :point="point" />
    <ComparativePhotos />
    <ArchivalMetadata :point="point" />
    <ExpeditionActivity />
    <DossierActions @open-upload="$emit('open-upload')" />
  </div>
</template>
