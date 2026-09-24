<script setup lang="ts">
import { computed } from 'vue'

import { formatNumber } from '@/core/format'
import type { SessionUser } from '@/core/session'
import MsIcon from '@/ui/MsIcon.vue'

import { ROLES, type HeroCounter } from '../data'

const props = defineProps<{
  /** null — модуль входа убран и человек не входил: показываем гостя. */
  user: SessionUser | null
  /** С `user_service` — подтверждён ли профиль администратором при одобрении заявки. */
  verified: boolean
  /** Когда профиль заведён — «В проекте с сентября 2026». */
  since: string | null
  /** «О себе» из профиля. Карточка — единственное место, где это видно. */
  bio: string
  counters: HeroCounter[]
  /** Есть ли что править: профиль живёт в аккаунте, у демо-входа его нет. */
  canEdit: boolean
}>()

defineEmits<{ edit: [] }>()

const sinceLabel = computed(() => {
  if (!props.since) return null
  const date = new Date(props.since)
  if (Number.isNaN(date.getTime())) return null
  // «сентября», а не «сентябрь»: месяц в родительном падеже Intl отдаёт только вместе с днём.
  const month = new Intl.DateTimeFormat('ru-RU', { day: 'numeric', month: 'long' }).format(date).replace(/^\d+\s*/, '')
  return `В проекте с ${month} ${date.getFullYear()}`
})

const role = computed(() => (props.user?.role ? ROLES[props.user.role] : null))

/**
 * Длинное имя в колонку между аватаром и кнопкой правки не влезает даже одним
 * словом, и браузер рвёт фамилию посередине. Такому имени даём кегль поменьше —
 * лучше мельче, но целиком.
 */
const longName = computed(() => (props.user?.name ?? '').split(' ').some((part) => part.length > 10))

/** Всё о человеке — в одной карточке: отдельных разделов «данные» и «учётная запись» на экране больше нет. */
const rows = computed(() =>
  props.canEdit
    ? [
        { id: 'bio', icon: 'description', label: 'О себе', value: props.bio || 'Пока ничего', multiline: true },
        { id: 'email', icon: 'mail', label: 'Почта для входа', value: props.user?.email ?? 'Демо-режим без аккаунта', multiline: false },
      ]
    : [],
)
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
          class="ribbon-shimmer hyphens-auto break-words text-on-surface [--shimmer-base:theme(colors.ink.DEFAULT)]"
          :class="
            longName
              ? 'font-headline-md text-headline-md'
              : 'font-headline-lg text-headline-lg short:text-headline-lg-mobile'
          "
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
        v-if="canEdit"
        type="button"
        aria-label="Изменить фото, имя и «о себе»"
        class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-surface-container-high text-on-surface active:scale-95"
        @click="$emit('edit')"
      >
        <MsIcon name="edit" :size="20" />
      </button>
    </div>

    <dl v-if="rows.length" class="flex flex-col gap-space-sm border-t border-outline-variant/60 pt-space-md">
      <div v-for="row in rows" :key="row.id" class="flex items-start gap-space-sm">
        <MsIcon :name="row.icon" :size="18" class="mt-0.5 shrink-0 text-on-surface-variant" />
        <div class="min-w-0">
          <dt class="font-label-sm text-label-sm text-on-surface-variant">{{ row.label }}</dt>
          <!-- «О себе» человек пишет абзацами, почта — одна строка, которой лучше обрезаться. -->
          <dd class="font-body-md text-body-md text-on-surface" :class="row.multiline ? 'whitespace-pre-line' : 'truncate'">{{ row.value }}</dd>
        </div>
      </div>
    </dl>

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
