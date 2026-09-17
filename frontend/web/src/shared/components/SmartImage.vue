<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  src: { type: String, default: '' },
  alt: { type: String, default: '' },
  icon: { type: String, default: 'image' },
  imgClass: { type: String, default: 'w-full h-full object-cover' },
})

const failed = ref(false)

watch(
  () => props.src,
  () => {
    failed.value = false
  },
)
</script>

<template>
  <img v-if="src && !failed" :src="src" :alt="alt" :class="imgClass" @error="failed = true" />
  <div v-else class="w-full h-full flex items-center justify-center">
    <span class="material-symbols-outlined text-on-surface-variant text-[32px]">{{ icon }}</span>
  </div>
</template>
