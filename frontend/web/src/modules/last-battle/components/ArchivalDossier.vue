<script setup>
import { computed } from 'vue'
import DossierHeader from './DossierHeader.vue'
import ComparativePhotos from './ComparativePhotos.vue'
import ArchivalMetadata from './ArchivalMetadata.vue'
import ExpeditionActivity from './ExpeditionActivity.vue'
import DossierActions from './DossierActions.vue'
import DossierStatusControls from './DossierStatusControls.vue'
import DirectionsButton from '@shared/components/DirectionsButton.vue'
import PointReviews from '@shared/components/PointReviews.vue'
import { useAuthSession } from '@modules/auth'

defineProps({
  point: { type: Object, default: null },
})
const emit = defineEmits(['open-upload', 'point-updated'])

const { session } = useAuthSession()

// Совпадает с _CURATOR_ROLES в map_service — менять статус может только модератор.
const canCurate = computed(() => session.user?.role === 'moderator' || session.user?.is_root)
</script>

<template>
  <div class="bg-surface-container-lowest rounded-lg p-6 shadow-md flex flex-col gap-5">
    <DossierHeader :point="point" />
    <DirectionsButton v-if="point" :point="point" />
    <DossierStatusControls v-if="canCurate && point" :point="point" @updated="emit('point-updated', $event)" />
    <ComparativePhotos />
    <ArchivalMetadata :point="point" />
    <PointReviews v-if="point" :point="point" />
    <ExpeditionActivity />
    <DossierActions @open-upload="$emit('open-upload')" />
  </div>
</template>
