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

const STATUS: Record<EntryStatus, { title: string; icon: string; class: string }> = {
  pending: { title: 'На проверке у краеведа', icon: 'hourglass_top', class: 'text-tertiary' },
  verified: { title: 'Подтверждено', icon: 'verified', class: 'text-secondary' },
  rejected: { title: 'Не подтверждено', icon: 'cancel', class: 'text-error' },
}

/** Карточка бойца заводится в «Памяти». Нет модуля — нет и кнопки. */
const canAdd = computed(() => router.hasRoute('memory'))

function addHero(): void {
  void router.push({ name: 'memory', query: { propose: 'soldier_card' } })
}
</script>

<template>
  <section class="flex flex-col gap-space-sm">
    <div class="flex items-center justify-between px-1">
      <div class="flex items-center gap-space-xs">
        <MsIcon name="account_tree" :size="20" class="text-primary" />
        <h3 class="font-headline-sm text-headline-sm text-on-surface">Герои семьи</h3>
      </div>
      <span
        v-if="entries"
        class="rounded-full bg-surface-container-high px-2 py-0.5 font-label-sm text-label-sm text-on-surface-variant"
      >
        {{ countLabel }}
      </span>
    </div>

    <p v-if="!entries" class="rounded-DEFAULT bg-surface-container-low p-space-md font-body-sm text-body-sm text-on-surface-variant">
      Народный архив сейчас не отвечает — карточки героев появятся, когда связь восстановится.
    </p>
    <p v-else-if="!heroes.length" class="rounded-DEFAULT bg-surface-container-low p-space-md font-body-sm text-body-sm text-on-surface-variant">
      Внесите карточку прадеда или прабабушки: краевед проверит её по Книге Памяти, и имя появится в народном архиве.
    </p>

    <div
      v-for="hero in heroes"
      :key="hero.id"
      class="flex items-center gap-space-md rounded-DEFAULT bg-surface-container-lowest p-space-md shadow-sm"
    >
      <div class="flex h-12 w-12 shrink-0 items-center justify-center rounded-DEFAULT bg-surface-container-high text-secondary">
        <MsIcon name="military_tech" :size="24" />
      </div>
      <div class="flex min-w-0 flex-col">
        <h4 class="truncate font-label-lg text-label-lg font-bold text-on-surface">{{ hero.title }}</h4>
        <span v-if="hero.date_text" class="truncate font-body-sm text-body-sm text-on-surface-variant">{{ hero.date_text }}</span>
        <span class="mt-0.5 flex items-center gap-1 font-label-sm text-label-sm" :class="STATUS[hero.status].class">
          <MsIcon :name="STATUS[hero.status].icon" :size="13" />
          {{ STATUS[hero.status].title }}
        </span>
      </div>
    </div>

    <button
      v-if="canAdd"
      type="button"
      class="flex w-full items-center justify-center gap-space-xs rounded-full bg-surface-container-high px-4 py-3 font-label-lg text-label-lg text-on-surface shadow-sm transition-colors hover:bg-surface-container-highest active:scale-[0.99]"
      @click="addHero"
    >
      <MsIcon name="person_add" :size="20" class="text-primary" />
      <span>Добавить героя в летопись</span>
    </button>
  </section>
</template>
