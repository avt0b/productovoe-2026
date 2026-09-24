<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'

import { plural } from '@/core/format'
import MsIcon from '@/ui/MsIcon.vue'

import { HERO_STATUS, type FamilyHero, type MyEntry } from '../data'
import HeroSheet from './HeroSheet.vue'

/**
 * Семейное древо: прадеды и прабабушки, которых помнят дома. Древо приватное —
 * его ведёт сам человек (`/family-heroes` в user_service), чужим оно не видно.
 *
 * Отдельно от него живёт народный архив: туда карточку бойца предлагают на
 * проверку краеведу, и уже она появляется в общей ленте. Поэтому здесь видно и
 * то, сколько карточек человек отправил в архив.
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

const countLabel = computed(
  () => `${props.heroes.length} ${plural(props.heroes.length, ['герой', 'героя', 'героев'])}`,
)

/** Сколько карточек бойцов человек уже отправил в народный архив. */
const cards = computed(() => (props.entries ?? []).filter((entry) => entry.kind === 'soldier_card'))

const years = (hero: FamilyHero): string =>
  [hero.birth_year, hero.death_year].some(Boolean) ? `${hero.birth_year ?? '?'} — ${hero.death_year ?? '?'}` : ''

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

    <p v-if="!heroes.length" class="rounded-2xl bg-surface-container-low p-space-md font-body-sm text-body-sm text-on-surface-variant">
      Внесите прадеда или прабабушку: имя, судьба, часть и то, что помнят дома. Древо видите только вы.
    </p>

    <ul v-else class="flex flex-col gap-space-xs">
      <li
        v-for="hero in heroes"
        :key="hero.id"
        class="flex items-center gap-space-sm rounded-2xl bg-surface-container-lowest p-space-sm shadow-document"
      >
        <span
          class="flex h-14 w-11 shrink-0 items-center justify-center overflow-hidden rounded-DEFAULT bg-surface-container-high text-on-surface-variant"
          aria-hidden="true"
        >
          <img v-if="hero.photo_url" :src="hero.photo_url" alt="" class="h-full w-full object-cover" loading="lazy" />
          <MsIcon v-else name="person" :size="22" />
        </span>
        <div class="flex min-w-0 flex-1 flex-col gap-0.5">
          <h3 class="truncate font-label-lg text-label-lg text-on-surface">{{ hero.name }}</h3>
          <span v-if="years(hero) || hero.unit" class="truncate font-body-sm text-body-sm text-on-surface-variant">
            {{ [years(hero), hero.unit].filter(Boolean).join(' · ') }}
          </span>
          <span
            class="flex items-center gap-1 self-start rounded-full px-2 py-0.5 font-label-sm text-label-sm"
            :class="HERO_STATUS[hero.status].tone"
          >
            <MsIcon :name="HERO_STATUS[hero.status].icon" :size="15" />
            {{ HERO_STATUS[hero.status].title }}
          </span>
        </div>
        <button
          type="button"
          :aria-label="`Изменить: ${hero.name}`"
          class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-surface-container-high text-on-surface active:scale-95"
          @click="open(hero)"
        >
          <MsIcon name="edit" :size="18" />
        </button>
      </li>
    </ul>

    <div class="flex flex-wrap gap-space-xs">
      <button
        type="button"
        class="flex items-center gap-space-xs rounded-full bg-surface-container-high px-space-md py-2 font-label-md text-label-md text-on-surface active:scale-95"
        @click="open(null)"
      >
        <MsIcon name="person_add" :size="18" />
        Добавить героя
      </button>
      <button
        v-if="canPropose"
        type="button"
        class="flex items-center gap-space-xs rounded-full bg-surface-container-high px-space-md py-2 font-label-md text-label-md text-on-surface active:scale-95"
        @click="proposeToArchive"
      >
        <MsIcon name="auto_stories" :size="18" />
        Карточка бойца в архив
      </button>
    </div>

    <p v-if="cards.length" class="font-body-sm text-body-sm text-on-surface-variant">
      В народный архив отправлено карточек бойцов: {{ cards.length }}. Их проверяет краевед.
    </p>

    <HeroSheet
      v-if="sheetOpen"
      :hero="edited"
      @close="sheetOpen = false"
      @saved="emit('changed')"
      @removed="emit('changed')"
    />
  </section>
</template>
