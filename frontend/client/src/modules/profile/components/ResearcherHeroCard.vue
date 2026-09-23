<script setup lang="ts">
import { computed } from 'vue'

import { formatNumber } from '@/core/format'
import type { SessionUser } from '@/core/session'
import MsIcon from '@/ui/MsIcon.vue'

import type { HeroCounter } from '../data'

const props = defineProps<{
  /** null — модуль входа убран и человек не входил: показываем гостя. */
  user: SessionUser | null
  /** С `user_service` — подтверждён ли профиль модератором или краеведом. */
  verified: boolean
  /** Когда профиль заведён — «В проекте с сентября 2026». */
  since: string | null
  counters: HeroCounter[]
}>()

defineEmits<{ 'open-token': [] }>()

const sinceLabel = computed(() => {
  if (!props.since) return null
  const date = new Date(props.since)
  if (Number.isNaN(date.getTime())) return null
  // «сентября», а не «сентябрь»: месяц в родительном падеже Intl отдаёт только вместе с днём.
  const month = new Intl.DateTimeFormat('ru-RU', { day: 'numeric', month: 'long' }).format(date).replace(/^\d+\s*/, '')
  return `В проекте с ${month} ${date.getFullYear()}`
})
</script>

<template>
  <div class="relative flex flex-col gap-space-lg overflow-hidden rounded-lg bg-secondary p-space-lg text-on-secondary shadow-lg">
    <div class="pointer-events-none absolute -bottom-10 -right-8 h-44 w-44 rounded-full bg-secondary-container/10 blur-xl" />
    <div class="pointer-events-none absolute -left-6 -top-6 h-32 w-32 rounded-full bg-surface-container-lowest/5" />

    <div class="relative z-10 flex items-start gap-space-md">
      <div class="relative shrink-0">
        <div class="flex h-16 w-16 items-center justify-center overflow-hidden rounded-full bg-secondary-fixed text-secondary shadow-md">
          <img v-if="user?.avatarUrl" :src="user.avatarUrl" alt="" class="h-full w-full object-cover" />
          <MsIcon v-else name="person" :size="32" />
        </div>
        <div
          v-if="verified"
          class="absolute -bottom-1 -right-1 flex h-6 w-6 items-center justify-center rounded-full bg-primary text-on-primary shadow-sm"
          title="Профиль подтверждён"
        >
          <MsIcon name="verified" :size="15" filled />
        </div>
      </div>

      <div class="flex min-w-0 flex-1 flex-col">
        <div class="flex items-center justify-between gap-space-xs">
          <h2 class="truncate font-headline-md text-headline-md leading-tight text-on-secondary">
            {{ user?.name ?? 'Гость' }}
          </h2>
          <button
            v-if="user"
            type="button"
            aria-label="Цифровой жетон исследователя"
            class="flex h-8 w-8 items-center justify-center rounded-full bg-on-secondary/15 transition-transform hover:bg-on-secondary/25 active:scale-95"
            @click="$emit('open-token')"
          >
            <MsIcon name="qr_code_2" :size="18" />
          </button>
        </div>
        <p class="mt-0.5 font-body-sm text-body-sm leading-snug text-secondary-fixed-dim">
          {{ user?.headline ?? 'Войдите, чтобы сохранять маршруты и находки' }}
        </p>
        <div v-if="user" class="mt-1.5 flex flex-wrap items-center gap-space-xs">
          <span
            v-if="user.city"
            class="inline-flex items-center gap-1 rounded-full bg-on-secondary/15 px-2 py-0.5 font-label-sm text-label-sm text-on-secondary"
          >
            <MsIcon name="location_on" :size="12" />
            {{ user.city }}
          </span>
          <span v-if="sinceLabel" class="font-label-sm text-label-sm text-secondary-fixed-dim">{{ sinceLabel }}</span>
        </div>
      </div>
    </div>

    <div class="relative z-10 grid grid-cols-3 gap-space-xs rounded-DEFAULT bg-on-secondary/10 p-space-sm backdrop-blur-sm">
      <div v-for="counter in counters" :key="counter.label" class="flex flex-col items-center px-1 py-0.5 text-center">
        <span
          class="font-headline-md text-headline-md font-bold"
          :class="counter.accent ? 'text-tertiary-fixed' : 'text-on-secondary'"
        >
          {{ formatNumber(counter.value) }}
        </span>
        <span class="mt-0.5 font-label-sm text-label-sm leading-tight text-secondary-fixed-dim">{{ counter.label }}</span>
      </div>
    </div>
  </div>
</template>
