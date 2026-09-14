<script setup lang="ts">
import { computed } from 'vue'

import { plural } from '@/core/format'
import MsIcon from '@/ui/MsIcon.vue'

import type { Ancestor } from '../data'

const props = defineProps<{ ancestors: Ancestor[] }>()

const countLabel = computed(
  () => `${props.ancestors.length} ${plural(props.ancestors.length, ['боец', 'бойца', 'бойцов'])}`,
)
</script>

<template>
  <section class="flex flex-col gap-space-sm">
    <div class="flex items-center justify-between px-1">
      <div class="flex items-center gap-space-xs">
        <MsIcon name="account_tree" :size="20" class="text-primary" />
        <h3 class="font-headline-sm text-headline-sm text-on-surface">Семейное древо и герои рода</h3>
      </div>
      <span class="rounded-full bg-surface-container-high px-2 py-0.5 font-label-sm text-label-sm text-on-surface-variant">
        {{ countLabel }}
      </span>
    </div>

    <div
      v-for="ancestor in ancestors"
      :key="ancestor.id"
      class="flex items-center justify-between gap-space-sm rounded-DEFAULT bg-surface-container-lowest p-space-md shadow-sm"
    >
      <div class="flex min-w-0 items-center gap-space-md">
        <div class="h-12 w-12 shrink-0 overflow-hidden rounded-DEFAULT bg-surface-container-high">
          <img :src="ancestor.photo" :alt="ancestor.name" class="h-full w-full object-cover" />
        </div>
        <div class="flex min-w-0 flex-col">
          <h4 class="truncate font-label-lg text-label-lg font-bold text-on-surface">{{ ancestor.name }}</h4>
          <span class="truncate font-body-sm text-body-sm text-on-surface-variant">{{ ancestor.lifespan }}</span>
          <div
            class="mt-0.5 flex items-center gap-1 font-label-sm text-label-sm"
            :class="ancestor.badgeTone === 'primary' ? 'text-primary' : 'text-secondary'"
          >
            <MsIcon :name="ancestor.badgeIcon" :size="13" />
            <span>{{ ancestor.badge }}</span>
          </div>
        </div>
      </div>
      <button
        type="button"
        :aria-label="`Карточка героя: ${ancestor.name}`"
        class="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-surface-container text-on-surface-variant hover:text-on-surface"
      >
        <MsIcon name="chevron_right" :size="18" />
      </button>
    </div>

    <button
      type="button"
      class="flex w-full items-center justify-center gap-space-xs rounded-full bg-surface-container-high px-4 py-3 font-label-lg text-label-lg text-on-surface shadow-sm transition-colors hover:bg-surface-container-highest active:scale-[0.99]"
    >
      <MsIcon name="person_add" :size="20" class="text-primary" />
      <span>Добавить предка в летопись</span>
    </button>
  </section>
</template>
