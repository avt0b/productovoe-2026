<script setup lang="ts">
import { computed } from 'vue'

import { formatDate } from '@/core/format'
import MsIcon from '@/ui/MsIcon.vue'

import { ACHIEVEMENTS, type Achievement, type MyEntry, type MyTrip } from '../data'

/**
 * Значки — только за то, что человек действительно сделал в сервисах. Главный
 * источник — `achievements` профиля: их выдаёт сервис, где случилось событие.
 * Старый user_service их не присылает — тогда значок выводим из активности.
 * Пока не заслужил — значок серый и подсказывает, как его получить.
 */
const props = defineProps<{
  achievements: Achievement[]
  trips: MyTrip[] | null
  entries: MyEntry[] | null
  excursions: number | null
  routesCompleted: number
}>()

interface Badge {
  id: string
  title: string
  hint: string
  icon: string
  tone: string
  earned: boolean
  /** Когда выдан сервисом; `null` — выведен из активности или ещё не получен. */
  earnedAt: string | null
}

const badges = computed<Badge[]>(() => {
  const awarded = new Map(props.achievements.map((item) => [item.code, item.earned_at]))
  const derived: Record<string, boolean> = {
    first_route_completed: props.routesCompleted > 0,
    trip_volunteer: (props.trips?.length ?? 0) > 0,
    archive_helper: (props.entries ?? []).some((entry) => entry.status === 'verified'),
    donor: false,
  }
  const known: Badge[] = Object.entries(ACHIEVEMENTS).map(([code, meta]) => ({
    id: code,
    ...meta,
    earned: awarded.has(code) || derived[code],
    earnedAt: awarded.get(code) ?? null,
  }))
  // Экскурсия с краеведом — значка у сервиса нет, но заслуга настоящая.
  known.push({
    id: 'excursion',
    title: 'Тропа памяти',
    hint: 'Экскурсия с краеведом',
    icon: 'groups',
    tone: 'bg-secondary-container text-on-secondary-container',
    earned: (props.excursions ?? 0) > 0,
    earnedAt: null,
  })
  // Новый код, о котором клиент ещё не знает, всё равно показываем — заслужен же.
  const unknown: Badge[] = props.achievements
    .filter((item) => !(item.code in ACHIEVEMENTS))
    .map((item) => ({
      id: item.code,
      title: item.code,
      hint: '',
      icon: 'military_tech',
      tone: 'bg-tertiary-fixed text-on-tertiary-fixed',
      earned: true,
      earnedAt: item.earned_at,
    }))
  return [...known, ...unknown].sort((a, b) => Number(b.earned) - Number(a.earned))
})

const earnedCount = computed(() => badges.value.filter((badge) => badge.earned).length)
</script>

<template>
  <section class="flex flex-col gap-space-sm">
    <div class="flex items-end justify-between gap-space-sm">
      <div>
        <p class="font-archival text-archival uppercase text-on-surface-variant">Награды</p>
        <h2 class="font-headline-md text-headline-md text-on-surface">Значки следопыта</h2>
      </div>
      <span class="rounded-full bg-tertiary-fixed px-2 py-0.5 font-label-sm text-label-sm text-on-tertiary-fixed">
        {{ earnedCount }} из {{ badges.length }}
      </span>
    </div>

    <ul class="grid grid-cols-3 gap-space-xs">
      <li
        v-for="badge in badges"
        :key="badge.id"
        class="flex flex-col items-center gap-1 rounded-2xl bg-surface-container-lowest p-space-sm text-center shadow-document"
      >
        <span
          class="flex h-12 w-12 items-center justify-center rounded-full"
          :class="badge.earned ? badge.tone : 'bg-surface-container-high text-on-surface-variant'"
          aria-hidden="true"
        >
          <MsIcon :name="badge.earned ? badge.icon : 'lock'" :size="24" :filled="badge.earned" />
        </span>
        <span class="font-label-sm text-label-sm leading-tight text-on-surface">{{ badge.title }}</span>
        <span class="font-label-sm text-label-sm font-normal leading-tight text-on-surface-variant">
          {{ badge.earned ? (badge.earnedAt ? formatDate(badge.earnedAt) : 'Получен') : badge.hint }}
        </span>
      </li>
    </ul>
  </section>
</template>
