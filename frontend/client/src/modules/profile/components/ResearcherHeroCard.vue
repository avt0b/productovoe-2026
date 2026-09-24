<script setup lang="ts">
import { computed } from 'vue'

import { formatNumber } from '@/core/format'
import type { SessionUser } from '@/core/session'
import MsIcon from '@/ui/MsIcon.vue'

import { ROLES, type HeroCounter } from '../data'

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

const role = computed(() => (props.user?.role ? ROLES[props.user.role] : null))
</script>

<template>
  <section class="flex flex-col gap-space-md rounded-2xl bg-surface-container-lowest p-space-md shadow-document">
    <div class="flex items-start gap-space-md">
      <div class="relative shrink-0">
        <div
          class="flex h-16 w-16 items-center justify-center overflow-hidden rounded-full bg-secondary-container text-on-secondary-container short:h-14 short:w-14"
        >
          <img v-if="user?.avatarUrl" :src="user.avatarUrl" alt="" class="h-full w-full object-cover" />
          <MsIcon v-else name="person" :size="28" />
        </div>
        <span
          v-if="verified"
          class="absolute -bottom-1 -right-1 flex h-6 w-6 items-center justify-center rounded-full bg-tertiary text-on-tertiary ring-2 ring-surface-container-lowest"
          title="Профиль подтверждён"
        >
          <MsIcon name="verified" :size="15" filled />
          <span class="sr-only">Профиль подтверждён</span>
        </span>
      </div>

      <div class="flex min-w-0 flex-1 flex-col gap-0.5">
        <p class="font-archival text-archival uppercase text-on-surface-variant">
          {{ role ? role.title : 'Исследователь' }}{{ verified ? ' · подтверждён' : '' }}
        </p>
        <h1
          class="ribbon-shimmer font-headline-lg [overflow-wrap:anywhere] text-headline-lg text-on-surface [--shimmer-base:theme(colors.ink.DEFAULT)] short:text-headline-lg-mobile"
        >
          {{ user?.name ?? 'Гость' }}
        </h1>
        <p class="font-body-sm text-body-sm text-on-surface-variant">
          {{ user?.headline || 'Войдите, чтобы сохранять маршруты и находки' }}
        </p>
        <div v-if="user && (user.city || sinceLabel)" class="mt-space-xs flex flex-wrap items-center gap-space-xs">
          <span
            v-if="user.city"
            class="flex items-center gap-1 rounded-full bg-surface-container-high px-2 py-0.5 font-label-sm text-label-sm text-on-surface"
          >
            <MsIcon name="location_on" :size="15" />
            {{ user.city }}
          </span>
          <span v-if="sinceLabel" class="font-label-sm text-label-sm text-on-surface-variant">{{ sinceLabel }}</span>
        </div>
      </div>

      <button
        v-if="user"
        type="button"
        aria-label="Жетон исследователя"
        class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-surface-container-high text-on-surface active:scale-95"
        @click="$emit('open-token')"
      >
        <MsIcon name="badge" :size="20" />
      </button>
    </div>

    <dl class="grid grid-cols-3 divide-x divide-outline-variant/60">
      <div v-for="counter in counters" :key="counter.label" class="flex flex-col-reverse items-center justify-end px-1 text-center">
        <dt class="font-label-sm text-label-sm leading-tight text-on-surface-variant">{{ counter.label }}</dt>
        <dd class="font-headline-md text-headline-md" :class="counter.accent ? 'text-tertiary' : 'text-on-surface'">
          {{ formatNumber(counter.value) }}
        </dd>
      </div>
    </dl>
  </section>
</template>
