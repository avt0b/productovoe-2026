<script setup lang="ts">
import { computed } from 'vue'

import { formatDate } from '@/core/format'
import MsIcon from '@/ui/MsIcon.vue'

import { ACHIEVEMENTS, type Achievement, type MyEntry, type MyTrip } from '../data'

/**
 * Значки — только за то, что человек действительно сделал в сервисах. Главный
 * источник — `achievements` профиля: их выдаёт сервис, где случилось событие.
 * Старый user_service их не присылает — тогда общий значок выводим из активности.
 * Пока не заслужил — значок серый и подсказывает, как его получить.
 *
 * У краеведа и поисковика — свой набор: за экскурсии и архив у одного, за
 * находки и выезды у другого. Он стоит первым: это то, ради чего роль выдана.
 */
const props = defineProps<{
  achievements: Achievement[]
  trips: MyTrip[] | null
  entries: MyEntry[] | null
  excursions: number | null
  routesCompleted: number
  /** Роль человека — от неё зависит, какой набор значков показать первым. */
  role?: string
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

const ROLE_BLOCK: Record<string, { rubric: string; title: string; icon: string }> = {
  local_historian: { rubric: 'Награды краеведа', title: 'Значки краеведа', icon: 'history_edu' },
  searcher: { rubric: 'Награды поисковика', title: 'Значки поисковика', icon: 'person_search' },
}

const awarded = computed(() => new Map(props.achievements.map((item) => [item.code, item.earned_at])))

function badge(code: string, derived = false): Badge {
  const meta = ACHIEVEMENTS[code]
  return {
    id: code,
    title: meta.title,
    hint: meta.hint,
    icon: meta.icon,
    tone: meta.tone,
    earned: awarded.value.has(code) || derived,
    earnedAt: awarded.value.get(code) ?? null,
  }
}

const earnedFirst = (a: Badge, b: Badge): number => Number(b.earned) - Number(a.earned)

const roleBlock = computed(() => (props.role ? (ROLE_BLOCK[props.role] ?? null) : null))

/** Значки своей роли — все, и полученные, и те, к которым идти. */
const roleBadges = computed<Badge[]>(() =>
  roleBlock.value
    ? Object.entries(ACHIEVEMENTS)
        .filter(([, meta]) => meta.role === props.role)
        .map(([code]) => badge(code))
    : [],
)
const roleEarned = computed(() => roleBadges.value.filter((item) => item.earned).length)

const commonBadges = computed<Badge[]>(() => {
  const derived: Record<string, boolean> = {
    first_route_completed: props.routesCompleted > 0,
    trip_volunteer: (props.trips?.length ?? 0) > 0,
    archive_helper: (props.entries ?? []).some((entry) => entry.status === 'verified'),
    donor: false,
  }
  const common = Object.entries(ACHIEVEMENTS)
    .filter(([, meta]) => !meta.role)
    .map(([code]) => badge(code, derived[code]))
  // Экскурсия с краеведом — значка у сервиса нет, но заслуга настоящая.
  common.push({
    id: 'excursion',
    title: 'Тропа памяти',
    hint: 'Экскурсия с краеведом',
    icon: 'groups',
    tone: 'bg-secondary-container text-on-secondary-container',
    earned: (props.excursions ?? 0) > 0,
    earnedAt: null,
  })
  // Заслуженные значки другой роли — краевед тоже может отметить находку. Показываем, раз получены.
  const foreign = Object.entries(ACHIEVEMENTS)
    .filter(([code, meta]) => meta.role && meta.role !== props.role && awarded.value.has(code))
    .map(([code]) => badge(code))
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
  return [...common, ...foreign, ...unknown].sort(earnedFirst)
})

const commonEarned = computed(() => commonBadges.value.filter((item) => item.earned).length)

function caption(item: Badge): string {
  if (!item.earned) return item.hint
  return item.earnedAt ? formatDate(item.earnedAt) : 'Получен'
}
</script>

<template>
  <!-- Свой набор роли — карточкой с прогрессом: это главные награды профиля. -->
  <section v-if="roleBlock" class="flex flex-col gap-space-sm">
    <div>
      <p class="font-archival text-archival uppercase text-on-surface-variant">{{ roleBlock.rubric }}</p>
      <h2 class="font-headline-md text-headline-md text-on-surface">{{ roleBlock.title }}</h2>
    </div>
    <div class="flex flex-col gap-space-md rounded-2xl bg-surface-container-lowest p-space-md shadow-document">
      <div class="flex items-center gap-space-sm">
        <span class="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-tertiary-fixed text-on-tertiary-fixed" aria-hidden="true">
          <MsIcon :name="roleBlock.icon" :size="22" filled />
        </span>
        <div class="flex min-w-0 flex-1 flex-col gap-1">
          <p class="font-label-lg text-label-lg text-on-surface">
            {{ roleEarned === roleBadges.length ? 'Все значки роли собраны' : `Получено ${roleEarned} из ${roleBadges.length}` }}
          </p>
          <div
            class="h-1.5 w-full overflow-hidden rounded-full bg-surface-container-high"
            role="progressbar"
            :aria-valuenow="roleEarned"
            aria-valuemin="0"
            :aria-valuemax="roleBadges.length"
            :aria-label="roleBlock.title"
          >
            <div
              class="h-full rounded-full bg-tertiary transition-[width] duration-500 ease-out"
              :style="{ width: `${roleBadges.length ? Math.round((roleEarned / roleBadges.length) * 100) : 0}%` }"
            />
          </div>
        </div>
      </div>

      <ul class="grid grid-cols-3 gap-space-xs">
        <li
          v-for="item in roleBadges"
          :key="item.id"
          class="flex flex-col items-center gap-1 rounded-2xl p-space-sm text-center"
          :class="item.earned ? 'bg-surface-container-low' : 'bg-surface-container-lowest ring-1 ring-outline-variant/50'"
        >
          <span
            class="flex h-12 w-12 items-center justify-center rounded-full"
            :class="item.earned ? item.tone : 'bg-surface-container-high text-outline'"
            aria-hidden="true"
          >
            <MsIcon :name="item.earned ? item.icon : 'lock'" :size="24" :filled="item.earned" />
          </span>
          <span class="font-label-sm text-label-sm leading-tight" :class="item.earned ? 'text-on-surface' : 'text-on-surface-variant'">
            {{ item.title }}
          </span>
          <span class="font-label-sm text-label-sm font-normal leading-tight text-on-surface-variant">{{ caption(item) }}</span>
        </li>
      </ul>
    </div>
  </section>

  <section class="flex flex-col gap-space-sm">
    <div class="flex items-end justify-between gap-space-sm">
      <div>
        <p class="font-archival text-archival uppercase text-on-surface-variant">Награды</p>
        <h2 class="font-headline-md text-headline-md text-on-surface">Значки следопыта</h2>
      </div>
      <span class="rounded-full bg-tertiary-fixed px-2 py-0.5 font-label-sm text-label-sm text-on-tertiary-fixed">
        {{ commonEarned }} из {{ commonBadges.length }}
      </span>
    </div>

    <ul class="grid grid-cols-3 gap-space-xs">
      <li
        v-for="item in commonBadges"
        :key="item.id"
        class="flex flex-col items-center gap-1 rounded-2xl bg-surface-container-lowest p-space-sm text-center shadow-document"
      >
        <span
          class="flex h-12 w-12 items-center justify-center rounded-full"
          :class="item.earned ? item.tone : 'bg-surface-container-high text-on-surface-variant'"
          aria-hidden="true"
        >
          <MsIcon :name="item.earned ? item.icon : 'lock'" :size="24" :filled="item.earned" />
        </span>
        <span class="font-label-sm text-label-sm leading-tight text-on-surface">{{ item.title }}</span>
        <span class="font-label-sm text-label-sm font-normal leading-tight text-on-surface-variant">{{ caption(item) }}</span>
      </li>
    </ul>
  </section>
</template>
