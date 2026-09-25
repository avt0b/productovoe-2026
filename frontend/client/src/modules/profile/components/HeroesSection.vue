<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'

import { plural } from '@/core/format'
import MsIcon from '@/ui/MsIcon.vue'

import { HERO_STATUS, HERO_STATUS_ORDER, type FamilyHero, type MyEntry } from '../data'
import HeroSheet from './HeroSheet.vue'

/**
 * Семейное древо: прадеды и прабабушки, которых помнят дома. Древо приватное —
 * его ведёт сам человек (`/family-heroes` в user_service), чужим оно не видно.
 *
 * Показываем летописью: герои по годам рождения на одной нити, у каждого —
 * портрет, годы, часть, судьба и строка из того, что помнят в семье.
 *
 * Отдельно от древа живёт народный архив: туда карточку бойца предлагают на
 * проверку краеведу. Поэтому внизу видно, сколько карточек уже отправлено.
 */
const props = defineProps<{
  heroes: FamilyHero[]
  /** Мои записи архива — из них считаем отправленные карточки бойцов. `null` — архив не ответил. */
  entries: MyEntry[] | null
}>()

const emit = defineEmits<{ changed: [] }>()

const router = useRouter()

const sheetOpen = ref(false)
const edited = ref<FamilyHero | null>(null)

/** Старшие — выше: летопись читается от прадеда к деду. Без года — в конце, в порядке добавления. */
const chronicle = computed(() =>
  [...props.heroes].sort((a, b) => (a.birth_year ?? Infinity) - (b.birth_year ?? Infinity) || a.created_at.localeCompare(b.created_at)),
)

const countLabel = computed(() => `${props.heroes.length} ${plural(props.heroes.length, ['герой', 'героя', 'героев'])}`)

/** Сводка судеб: сколько вернулись, сколько погибли, скольких ещё ищут. */
const fates = computed(() =>
  HERO_STATUS_ORDER.map((status) => ({ status, count: props.heroes.filter((hero) => hero.status === status).length })).filter(
    (item) => item.count > 0,
  ),
)

/** Сколько карточек бойцов человек уже отправил в народный архив. */
const cards = computed(() => (props.entries ?? []).filter((entry) => entry.kind === 'soldier_card'))

function years(hero: FamilyHero): string {
  if (!hero.birth_year && !hero.death_year) return 'Годы жизни неизвестны'
  return `${hero.birth_year ?? '?'} — ${hero.death_year ?? (hero.status === 'veteran' ? '' : '?')}`.trim()
}

/** Инициалы вместо пустого силуэта: «Воронов Алексей Григорьевич» → «ВА». */
function initials(name: string): string {
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() ?? '')
    .join('')
}

/** Карточка бойца заводится в «Памяти». Нет модуля — нет и кнопки. */
const canPropose = computed(() => router.hasRoute('memory'))

function open(hero: FamilyHero | null): void {
  edited.value = hero
  sheetOpen.value = true
}

function proposeToArchive(): void {
  void router.push({ name: 'memory', query: { propose: 'soldier_card' } })
}
</script>

<template>
  <section class="flex flex-col gap-space-sm">
    <div class="flex items-end justify-between gap-space-sm">
      <div>
        <p class="font-archival text-archival uppercase text-on-surface-variant">Летопись семьи</p>
        <h2 class="font-headline-md text-headline-md text-on-surface">Герои семьи</h2>
      </div>
      <span
        v-if="heroes.length"
        class="rounded-full bg-surface-container-high px-2 py-0.5 font-label-sm text-label-sm text-on-surface-variant"
      >
        {{ countLabel }}
      </span>
    </div>

    <div class="flex flex-col gap-space-md rounded-2xl bg-surface-container-lowest p-space-md shadow-document">
      <!-- Пусто — приглашение начать летопись, а не серая строка. -->
      <div v-if="!heroes.length" class="flex flex-col items-center gap-space-sm py-space-sm text-center">
        <span class="flex h-14 w-14 items-center justify-center rounded-full bg-tertiary-fixed text-on-tertiary-fixed" aria-hidden="true">
          <MsIcon name="auto_stories" :size="28" />
        </span>
        <p class="max-w-[30ch] font-body-sm text-body-sm text-on-surface-variant">
          Начните летопись: внесите прадеда или прабабушку — имя, судьбу, часть и то, что помнят дома. Её видите только вы.
        </p>
      </div>

      <template v-else>
        <ul v-if="fates.length > 1" class="flex flex-wrap gap-space-xs" aria-label="Судьбы героев">
          <li
            v-for="fate in fates"
            :key="fate.status"
            class="flex items-center gap-1 rounded-full px-2 py-0.5 font-label-sm text-label-sm"
            :class="HERO_STATUS[fate.status].tone"
          >
            <MsIcon :name="HERO_STATUS[fate.status].icon" :size="15" />
            {{ HERO_STATUS[fate.status].title }}: {{ fate.count }}
          </li>
        </ul>

        <ol class="relative flex flex-col gap-space-md">
          <!-- Нить летописи: портреты нанизаны на неё по старшинству. -->
          <span v-if="chronicle.length > 1" class="absolute bottom-6 left-7 top-6 w-0.5 bg-outline-variant/60" aria-hidden="true" />
          <li v-for="hero in chronicle" :key="hero.id" class="relative">
            <button
              type="button"
              class="flex w-full items-start gap-space-md rounded-2xl text-left transition-colors hover:bg-surface-container-low active:scale-[0.99]"
              :aria-label="`${hero.name}: изменить`"
              @click="open(hero)"
            >
              <span
                class="relative flex h-[4.5rem] w-14 shrink-0 items-center justify-center overflow-hidden rounded-2xl bg-surface-container-high font-headline-sm text-headline-sm text-on-surface-variant ring-4 ring-surface-container-lowest"
                aria-hidden="true"
              >
                <img v-if="hero.photo_url" :src="hero.photo_url" alt="" class="h-full w-full object-cover" loading="lazy" />
                <template v-else>{{ initials(hero.name) || '?' }}</template>
              </span>
              <span class="flex min-w-0 flex-1 flex-col gap-1 py-0.5">
                <span class="font-archival text-archival uppercase text-secondary">{{ years(hero) }}</span>
                <span class="font-headline-sm text-headline-sm text-on-surface">{{ hero.name }}</span>
                <span v-if="hero.unit" class="flex items-center gap-1 font-body-sm text-body-sm text-on-surface-variant">
                  <MsIcon name="flag" :size="15" class="shrink-0 text-secondary" />
                  <span class="truncate">{{ hero.unit }}</span>
                </span>
                <span class="flex items-center gap-1 self-start rounded-full px-2 py-0.5 font-label-sm text-label-sm" :class="HERO_STATUS[hero.status].tone">
                  <MsIcon :name="HERO_STATUS[hero.status].icon" :size="15" />
                  {{ HERO_STATUS[hero.status].title }}
                </span>
                <span v-if="hero.note" class="line-clamp-2 border-l-2 border-tertiary-fixed-dim pl-space-sm font-body-sm text-body-sm italic text-on-surface-variant">
                  {{ hero.note }}
                </span>
              </span>
              <MsIcon name="edit" :size="18" class="mt-1 shrink-0 text-outline" />
            </button>
          </li>
        </ol>
      </template>

      <div class="flex flex-col gap-space-xs border-t border-outline-variant/40 pt-space-md">
        <button
          type="button"
          class="flex w-full items-center justify-center gap-space-xs rounded-full bg-secondary px-space-md py-2.5 font-label-lg text-label-lg text-on-secondary active:scale-[0.99]"
          @click="open(null)"
        >
          <MsIcon name="person_add" :size="18" />
          {{ heroes.length ? 'Добавить героя' : 'Внести первого героя' }}
        </button>
        <button
          v-if="canPropose"
          type="button"
          class="flex items-center justify-center gap-space-xs rounded-full bg-surface-container-high px-space-md py-2 font-label-md text-label-md text-on-surface active:scale-95"
          @click="proposeToArchive"
        >
          <MsIcon name="auto_stories" :size="18" />
          Карточка бойца в народный архив
        </button>
        <p v-if="cards.length" class="flex items-center justify-center gap-1 text-center font-body-sm text-body-sm text-on-surface-variant">
          <MsIcon name="fact_check" :size="15" class="shrink-0" />
          В архив отправлено карточек: {{ cards.length }} — их проверяет краевед
        </p>
      </div>
    </div>

    <HeroSheet
      v-if="sheetOpen"
      :hero="edited"
      @close="sheetOpen = false"
      @saved="emit('changed')"
      @removed="emit('changed')"
    />
  </section>
</template>
