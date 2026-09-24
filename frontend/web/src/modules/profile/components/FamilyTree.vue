<script setup>
import { ref } from 'vue'
import SmartImage from '@shared/components/SmartImage.vue'
import { useAuthSession } from '@modules/auth'
import { useProfileStore } from '../profileStore.js'
import FamilyHeroModal from './FamilyHeroModal.vue'
import HeroDossierModal from './HeroDossierModal.vue'

// user_service: FamilyHero — приватная история семьи (не путать с
// «Живой памятью»/народным архивом: там публичные записи с верификацией
// краеведом, тут видно только владельцу и его гостям на профиле, а
// редактирует только владелец). Список приходит вместе с профилем
// (ProfileOut.heroes).
const { session } = useAuthSession()
const { profile, loadMyProfile } = useProfileStore()

const STATUS_META = {
  killed_in_action: { label: 'Погиб в бою', class: 'bg-primary-fixed text-on-primary-fixed' },
  missing_in_action: { label: 'Пропал без вести', class: 'bg-tertiary-fixed text-on-tertiary-fixed' },
  died_of_wounds: { label: 'Умер от ран', class: 'bg-error-container text-on-error-container' },
  veteran: { label: 'Ветеран', class: 'bg-secondary-fixed text-on-secondary-fixed' },
}

function yearsLabel(hero) {
  const parts = []
  if (hero.birth_year || hero.death_year) parts.push(`${hero.birth_year ?? '?'} – ${hero.death_year ?? '?'}`)
  if (hero.unit) parts.push(hero.unit)
  return parts.join(' • ')
}

const modalOpen = ref(false)
const editingHero = ref(null)
const dossierOpen = ref(false)
const dossierHero = ref(null)

function openCreate() {
  editingHero.value = null
  modalOpen.value = true
}

function openEdit(hero) {
  dossierOpen.value = false
  editingHero.value = hero
  modalOpen.value = true
}

function openDossier(hero) {
  dossierHero.value = hero
  dossierOpen.value = true
}

// Проще перечитать профиль целиком, чем вести отдельное состояние списка —
// он и так уже дружит с остальной шапкой профиля (счётчики и т.п.).
function onChanged() {
  loadMyProfile()
}
</script>

<template>
  <div class="bg-surface-container-lowest p-6 rounded-2xl shadow-document flex flex-col">
    <div class="flex items-center justify-between gap-4 mb-6">
      <div class="flex items-center gap-3">
        <div class="w-10 h-10 rounded-full bg-secondary-container text-on-secondary-container flex items-center justify-center">
          <span class="material-symbols-outlined text-[20px]">diversity_3</span>
        </div>
        <div class="flex flex-col">
          <h2 class="font-headline-sm text-headline-sm font-bold text-on-surface">Семейное древо и герои рода</h2>
          <span class="font-body-sm text-body-sm text-on-surface-variant">user_service, family_heroes — видно только вам</span>
        </div>
      </div>
      <button
        v-if="session.status === 'authenticated'"
        class="bg-secondary-fixed hover:bg-secondary-fixed-dim text-on-secondary-fixed font-label-md text-label-md font-bold px-4 py-2 rounded-full transition-all flex items-center gap-1.5 shadow-sm"
        @click="openCreate"
      >
        <span class="material-symbols-outlined text-[18px]">add</span>
        <span class="hidden sm:inline">Добавить предка</span>
      </button>
    </div>

    <p v-if="session.status !== 'authenticated'" class="font-body-sm text-body-sm text-on-surface-variant">
      Войдите, чтобы добавить героев своей семьи.
    </p>
    <p v-else-if="!profile.data?.heroes?.length" class="font-body-sm text-body-sm text-on-surface-variant">
      Пока никого не добавили — начните с первого героя семьи.
    </p>

    <div v-else class="flex flex-col gap-4">
      <button
        v-for="hero in profile.data.heroes"
        :key="hero.id"
        type="button"
        class="text-left bg-surface-container-low p-4 rounded-DEFAULT flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 hover:bg-surface-container transition-colors"
        @click="openDossier(hero)"
      >
        <div class="flex items-center gap-4 min-w-0">
          <div class="w-16 h-16 rounded-DEFAULT overflow-hidden bg-surface-container-high shrink-0 shadow-sm">
            <SmartImage :src="hero.photo_url" icon="portrait" />
          </div>
          <div class="flex flex-col min-w-0">
            <div class="flex items-center gap-2 flex-wrap">
              <h3 class="font-headline-sm text-headline-sm text-on-surface font-bold truncate">{{ hero.name }}</h3>
              <span class="text-[11px] font-bold px-2 py-0.5 rounded-full uppercase shrink-0" :class="STATUS_META[hero.status]?.class">
                {{ STATUS_META[hero.status]?.label ?? hero.status }}
              </span>
            </div>
            <p v-if="yearsLabel(hero)" class="font-body-sm text-body-sm text-on-surface-variant mt-0.5">{{ yearsLabel(hero) }}</p>
            <p v-if="hero.note" class="font-label-sm text-label-sm font-bold text-secondary mt-2">{{ hero.note }}</p>
          </div>
        </div>
        <span
          class="bg-surface-container-lowest text-on-surface hover:bg-surface-container-high px-3.5 py-1.5 rounded-full font-label-sm text-label-sm font-bold shadow-sm flex items-center gap-1 shrink-0"
          @click.stop="openEdit(hero)"
        >
          <span>Изменить</span>
          <span class="material-symbols-outlined text-[16px]">edit</span>
        </span>
      </button>
    </div>

    <HeroDossierModal v-model="dossierOpen" :hero="dossierHero" @edit="openEdit" />
    <FamilyHeroModal v-model="modalOpen" :hero="editingHero" @saved="onChanged" @deleted="onChanged" />
  </div>
</template>
