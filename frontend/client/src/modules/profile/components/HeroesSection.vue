<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'

import { plural } from '@/core/format'
import MsIcon from '@/ui/MsIcon.vue'

import type { EntryStatus, MyEntry } from '../data'

/**
 * Герои семьи — карточки бойцов, которые человек сам внёс в народный архив.
 * Краевед проверяет карточку, и она появляется в общей ленте с отметкой
 * «Подтверждено».
 */
const props = defineProps<{
  /** `null` — архив не ответил. */
  entries: MyEntry[] | null
}>()

const router = useRouter()

const heroes = computed(() => (props.entries ?? []).filter((entry) => entry.kind === 'soldier_card'))
const countLabel = computed(() => `${heroes.value.length} ${plural(heroes.value.length, ['боец', 'бойца', 'бойцов'])}`)

/** «Подтверждено» — латунью, как на карточках архива. */
const STATUS: Record<EntryStatus, { title: string; icon: string; class: string }> = {
  pending: { title: 'На проверке у краеведа', icon: 'hourglass_top', class: 'bg-surface-container-high text-on-surface-variant' },
  verified: { title: 'Подтверждено', icon: 'verified', class: 'bg-tertiary-fixed text-on-tertiary-fixed' },
  rejected: { title: 'Не подтверждено', icon: 'cancel', class: 'bg-error-container text-on-error-container' },
}

/** Карточка бойца заводится в «Памяти». Нет модуля — нет и кнопки. */
const canAdd = computed(() => router.hasRoute('memory'))

function addHero(): void {
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
      <span v-if="entries" class="rounded-full bg-surface-container-high px-2 py-0.5 font-label-sm text-label-sm text-on-surface-variant">
        {{ countLabel }}
      </span>
    </div>

    <p v-if="!entries" class="rounded-2xl bg-surface-container-low p-space-md font-body-sm text-body-sm text-on-surface-variant">
      Народный архив сейчас не отвечает — карточки героев появятся, когда связь восстановится.
    </p>
    <p v-else-if="!heroes.length" class="rounded-2xl bg-surface-container-low p-space-md font-body-sm text-body-sm text-on-surface-variant">
      Внесите карточку прадеда или прабабушки: краевед проверит её по Книге Памяти, и имя появится в народном архиве.
    </p>

    <ul v-if="heroes.length" class="flex flex-col gap-space-xs">
      <li v-for="hero in heroes" :key="hero.id" class="flex items-center gap-space-sm rounded-2xl bg-surface-container-lowest p-space-sm shadow-document">
        <span class="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-surface-container-high text-on-surface-variant" aria-hidden="true">
          <MsIcon name="military_tech" :size="22" />
        </span>
        <div class="flex min-w-0 flex-1 flex-col gap-0.5">
          <h3 class="truncate font-label-lg text-label-lg text-on-surface">{{ hero.title }}</h3>
          <span v-if="hero.date_text" class="truncate font-body-sm text-body-sm text-on-surface-variant">{{ hero.date_text }}</span>
          <span class="flex items-center gap-1 self-start rounded-full px-2 py-0.5 font-label-sm text-label-sm" :class="STATUS[hero.status].class">
            <MsIcon :name="STATUS[hero.status].icon" :size="15" :filled="hero.status === 'verified'" />
            {{ STATUS[hero.status].title }}
          </span>
        </div>
      </li>
    </ul>

    <button
      v-if="canAdd"
      type="button"
      class="flex items-center justify-center gap-space-xs self-start rounded-full bg-surface-container-high px-space-md py-2 font-label-md text-label-md text-on-surface active:scale-95"
      @click="addHero"
    >
      <MsIcon name="person_add" :size="18" />
      Добавить героя в летопись
    </button>
  </section>
</template>
