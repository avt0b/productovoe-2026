<script setup lang="ts">
import { computed, ref, watch } from 'vue'

import MsIcon from '@/ui/MsIcon.vue'

import { ACHIEVEMENTS, type Achievement, type MyEntry, type MyTrip } from '../data'

/**
 * Профиль-игра для семейного и детского режима (`usePreferencesStore().familyMode`,
 * решает вызывающая сторона — `ProfilePage.vue`). Звание и прогресс считаем
 * только из того, что уже реально отдают сервисы: значки, пройденные
 * маршруты, выезды, записи архива, экскурсии — те же данные, что уже
 * приходят в `BadgesSection.vue`. Никаких выдуманных очков.
 */
const props = defineProps<{
  achievements: Achievement[]
  trips: MyTrip[] | null
  entries: MyEntry[] | null
  excursions: number | null
  routesCompleted: number
  role?: string
}>()

/** Коды из ACHIEVEMENTS, применимые к человеку: общие + свои по роли. */
const applicableCodes = computed(() =>
  Object.entries(ACHIEVEMENTS)
    .filter(([, meta]) => !meta.role || meta.role === props.role)
    .map(([code]) => code),
)

const awardedCodes = computed(() => new Set(props.achievements.map((item) => item.code)))

/** То же дублирование производного статуса, что в BadgesSection.vue — своих данных сервис не даёт. */
const derived: Record<string, boolean> = {
  first_route_completed: false,
  trip_volunteer: false,
  archive_helper: false,
}
const derivedNow = computed<Record<string, boolean>>(() => ({
  ...derived,
  first_route_completed: props.routesCompleted > 0,
  trip_volunteer: (props.trips?.length ?? 0) > 0,
  archive_helper: (props.entries ?? []).some((entry) => entry.status === 'verified'),
}))

const earnedCodes = computed(() => {
  const set = new Set<string>()
  for (const code of applicableCodes.value) {
    if (awardedCodes.value.has(code) || derivedNow.value[code]) set.add(code)
  }
  // Экскурсия с краеведом — как в BadgesSection.vue, значка у сервиса для неё нет.
  if ((props.excursions ?? 0) > 0) set.add('excursion')
  return set
})

const totalCount = computed(() => applicableCodes.value.length + 1)
const earnedCount = computed(() => earnedCodes.value.size)

interface Rank {
  title: string
  icon: string
}

/** Пороги — доля собранных значков, не абсолютные числа: набор роли и без роли разного размера. */
const RANKS: readonly (Rank & { atLeast: number })[] = [
  { atLeast: 0, title: 'Юный следопыт', icon: 'explore' },
  { atLeast: 0.34, title: 'Разведчик', icon: 'travel_explore' },
  { atLeast: 0.7, title: 'Хранитель памяти', icon: 'military_tech' },
]

const progress = computed(() => (totalCount.value ? earnedCount.value / totalCount.value : 0))
const rankIndex = computed(() => RANKS.reduce((acc, rank, index) => (progress.value >= rank.atLeast ? index : acc), 0))
const rank = computed(() => RANKS[rankIndex.value])
const nextRank = computed(() => RANKS[rankIndex.value + 1] ?? null)
const toNext = computed(() => {
  if (!nextRank.value) return null
  const need = Math.ceil(nextRank.value.atLeast * totalCount.value) - earnedCount.value
  return Math.max(1, need)
})

/** Одно необязательное действие из того, чего человек ещё не сделал — с честной подсказкой сервиса. */
const QUEST_ROUTES: Record<string, string> = {
  first_route_completed: 'routes',
  trip_volunteer: 'hq',
  archive_helper: 'memory',
  donor: 'hq',
  excursion: 'excursions',
  historian_first_excursion: 'excursions',
  historian_led_group: 'excursions',
  historian_five_stars: 'excursions',
  historian_route_author: 'my-routes',
  historian_poi_author: 'routes',
  historian_archive_keeper: 'memory',
  searcher_squad_founder: 'hq',
  searcher_trip_organizer: 'hq',
  searcher_first_find: 'last-stand',
  searcher_archive_confirmed: 'last-stand',
  searcher_remains_raised: 'last-stand',
  searcher_goal_reached: 'hq',
}

const EXCURSION_META = { title: 'Тропа памяти', hint: 'Экскурсия с краеведом', icon: 'groups' }

const quest = computed(() => {
  const code = applicableCodes.value.find((item) => !earnedCodes.value.has(item) && item in QUEST_ROUTES)
  if (code) {
    const meta = ACHIEVEMENTS[code]
    return { code, title: meta.hint, icon: meta.icon, route: QUEST_ROUTES[code] }
  }
  if (!earnedCodes.value.has('excursion')) {
    return { code: 'excursion', title: EXCURSION_META.hint, icon: EXCURSION_META.icon, route: QUEST_ROUTES.excursion }
  }
  return null
})

// --- праздник при новом значке ---

const SEEN_KEY = 'marshruty.client.badges-seen'
function readSeen(): Set<string> {
  try {
    return new Set(JSON.parse(localStorage.getItem(SEEN_KEY) ?? '[]') as string[])
  } catch {
    return new Set()
  }
}
function writeSeen(codes: Set<string>): void {
  try {
    localStorage.setItem(SEEN_KEY, JSON.stringify([...codes]))
  } catch {
    /* приватный режим — в следующий раз отметим снова, не страшно */
  }
}

const celebrating = ref<{ title: string; icon: string } | null>(null)
let celebrateTimer: ReturnType<typeof setTimeout> | undefined

/**
 * Празднуем только по-настоящему выданные значки (`props.achievements`), не
 * выведенные на клиенте: производный статус — не событие, а слепок текущих
 * данных, «новым» его считать нечестно.
 */
watch(
  () => props.achievements.map((item) => item.code),
  (codes) => {
    if (!codes.length) return
    const seen = readSeen()
    const fresh = codes.find((code) => !seen.has(code))
    if (!fresh) {
      writeSeen(new Set(codes))
      return
    }
    const meta = ACHIEVEMENTS[fresh]
    celebrating.value = meta ? { title: meta.title, icon: meta.icon } : { title: fresh, icon: 'military_tech' }
    writeSeen(new Set([...seen, ...codes]))
    clearTimeout(celebrateTimer)
    celebrateTimer = setTimeout(() => (celebrating.value = null), 2600)
  },
  { immediate: true },
)
</script>

<template>
  <section class="relative flex flex-col gap-space-sm">
    <div>
      <p class="font-archival text-archival uppercase text-on-surface-variant">Игра следопыта</p>
      <h2 class="font-headline-md text-headline-md text-on-surface">Звание и задание дня</h2>
    </div>

    <div class="flex flex-col gap-space-md rounded-2xl bg-surface-container-lowest p-space-md shadow-document">
      <div class="flex items-center gap-space-sm">
        <span class="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-tertiary-fixed text-on-tertiary-fixed" aria-hidden="true">
          <MsIcon :name="rank.icon" :size="24" filled />
        </span>
        <div class="min-w-0 flex-1">
          <p class="font-headline-sm text-headline-sm text-on-surface">{{ rank.title }}</p>
          <p class="font-body-sm text-body-sm text-on-surface-variant">
            {{ toNext ? `До «${nextRank!.title}» — ещё ${toNext} ${toNext === 1 ? 'значок' : 'значка'}` : 'Высшее звание — все значки собраны' }}
          </p>
        </div>
      </div>

      <div class="h-2 w-full overflow-hidden rounded-full bg-surface-container-high" role="progressbar" :aria-valuenow="earnedCount" aria-valuemin="0" :aria-valuemax="totalCount" aria-label="Прогресс звания">
        <div class="h-full rounded-full bg-tertiary transition-[width] duration-500 ease-out" :style="{ width: `${Math.round(progress * 100)}%` }" />
      </div>

      <RouterLink
        v-if="quest"
        :to="{ name: quest.route }"
        class="flex items-center gap-space-sm rounded-2xl bg-secondary-container/60 p-space-sm active:scale-[0.99]"
      >
        <span class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-secondary text-on-secondary" aria-hidden="true">
          <MsIcon :name="quest.icon" :size="20" />
        </span>
        <span class="min-w-0 flex-1">
          <span class="block font-archival text-archival uppercase text-on-surface-variant">Задание дня</span>
          <span class="block font-label-lg text-label-lg text-on-surface">{{ quest.title }}</span>
        </span>
        <MsIcon name="chevron_right" :size="20" class="shrink-0 text-on-surface-variant" />
      </RouterLink>
      <p v-else class="text-center font-body-sm text-body-sm text-on-surface-variant">Все задания на сейчас выполнены — загляните завтра</p>
    </div>

    <!-- Праздник: короткая анимация без звука, statична при prefers-reduced-motion. -->
    <Teleport to="body">
      <Transition name="badge-pop">
        <div v-if="celebrating" class="badge-celebration pt-safe" role="status" aria-live="polite">
          <div class="mx-margin mt-space-lg flex items-center gap-space-sm rounded-2xl bg-tertiary-fixed p-space-md shadow-sheet">
            <span class="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-tertiary text-on-tertiary" aria-hidden="true">
              <MsIcon :name="celebrating.icon" :size="26" filled />
            </span>
            <div class="min-w-0">
              <p class="font-archival text-archival uppercase text-on-tertiary-fixed-variant">Новый значок!</p>
              <p class="font-headline-sm text-headline-sm text-on-tertiary-fixed">{{ celebrating.title }}</p>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </section>
</template>

<style scoped>
.badge-celebration {
  position: fixed;
  inset: 0 0 auto;
  z-index: 1600;
}

.badge-pop-enter-active {
  transition:
    transform 320ms cubic-bezier(0.34, 1.56, 0.64, 1),
    opacity 200ms ease-out;
}
.badge-pop-leave-active {
  transition:
    transform 220ms ease-in,
    opacity 220ms ease-in;
}
.badge-pop-enter-from,
.badge-pop-leave-to {
  transform: translateY(-16px) scale(0.96);
  opacity: 0;
}

@media (prefers-reduced-motion: reduce) {
  .badge-pop-enter-active,
  .badge-pop-leave-active {
    transition: opacity 150ms linear;
  }
  .badge-pop-enter-from,
  .badge-pop-leave-to {
    transform: none;
  }
}
</style>
