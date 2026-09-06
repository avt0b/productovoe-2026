<script setup lang="ts">
withDefaults(defineProps<{ eyebrow?: string; title: string; subtitle?: string }>(), {
  eyebrow: '',
  subtitle: '',
})
</script>

<template>
  <div class="flex flex-col gap-space-4 pb-space-6 md:flex-row md:items-end md:justify-between">
    <div class="flex max-w-3xl flex-col gap-space-1">
      <span
        v-if="eyebrow"
        class="font-label-archive-code text-label-archive-code uppercase tracking-widest text-primary"
      >
        {{ eyebrow }}
      </span>
      <h1 class="font-headline-lg text-headline-lg uppercase tracking-wide text-on-surface">
        {{ title }}
      </h1>
      <p v-if="subtitle" class="font-body-md text-body-md text-on-surface-variant">
        {{ subtitle }}
      </p>
    </div>
    <div class="flex flex-wrap items-center gap-space-3">
      <slot name="actions" />
    </div>
  </div>
</template>
