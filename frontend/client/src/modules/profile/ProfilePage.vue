<script setup lang="ts">
import { computed, ref, watch } from 'vue'

import { useAsync } from '@/core/async'
import { useSessionStore } from '@/core/session'
import AccountRequired from '@/ui/AccountRequired.vue'
import StateBlock from '@/ui/StateBlock.vue'

import BadgesSection from './components/BadgesSection.vue'
import ExpeditionStatusCard from './components/ExpeditionStatusCard.vue'
import HeroesSection from './components/HeroesSection.vue'
import ProfileEditSheet from './components/ProfileEditSheet.vue'
import ResearcherHeroCard from './components/ResearcherHeroCard.vue'
import ResearcherTokenModal from './components/ResearcherTokenModal.vue'
import RoleRequestSection from './components/RoleRequestSection.vue'
import RolesSection from './components/RolesSection.vue'
import SettingsSection from './components/SettingsSection.vue'
import SupportSection from './components/SupportSection.vue'
import { fetchProfile, nextTrip, type HeroCounter, type Profile, type ProfileOverview } from './data'

const session = useSessionStore()

/** Демо-режим без аккаунта: профиля в `user_service` нет, показываем гостя и семейный режим. */
const overview = useAsync<ProfileOverview | null>(() => (session.hasAccount ? fetchProfile() : Promise.resolve(null)))
const { data, loading, error, retry } = overview

/** Правка фото, имени, города и «о себе» — одно окно на весь экран профиля. */
const editOpen = ref(false)
const tokenOpen = ref(false)

/** Имя, город и фото приходят из профиля — сессия их узнаёт, чтобы шапка и аватар показывали то же. */
watch(
  () => data.value?.profile,
  (profile) => {
    if (!profile) return
    session.updateUser({
      ...(profile.display_name ? { name: profile.display_name } : {}),
      city: profile.city,
      // Фото сняли — в сессии его тоже быть не должно.
      avatarUrl: profile.avatar_url ?? undefined,
    })
  },
)

/** Сохранённый профиль — в экран; сессию догонит наблюдатель выше. */
function applyProfile(profile: Profile): void {
  // Значки и счётчики сервис заполняет только в GET — ответ PUT принёс бы пустые и затёр бы их.
  const { achievements, routes_completed, excursions_completed, finds_count, ...fields } = profile
  if (data.value) data.value = { ...data.value, profile: { ...data.value.profile, ...fields } }
}

const counters = computed<HeroCounter[]>(() => [
  { value: data.value?.trips?.length ?? null, label: 'выездов с отрядом' },
  { value: data.value?.entries?.length ?? null, label: 'записей в архиве' },
  { value: data.value?.excursions ?? data.value?.profile.excursions_completed ?? null, label: 'экскурсий', accent: true },
])
</script>

<template>
  <div class="flex w-full flex-col gap-space-md px-margin short:gap-space-sm">
    <StateBlock v-if="loading || error" :loading="loading" :error="error" @retry="retry" />

    <template v-else>
      <ResearcherHeroCard
        :user="session.user"
        :verified="data?.profile.is_verified ?? false"
        :since="data?.profile.created_at ?? null"
        :bio="data?.profile.bio ?? ''"
        :counters="counters"
        :can-edit="data !== null"
        @edit="editOpen = true"
      />

      <template v-if="data">
        <ExpeditionStatusCard :trip="nextTrip(data.trips)" />
        <RolesSection v-if="session.user" :user="session.user" @open-token="tokenOpen = true" />
        <RoleRequestSection v-if="session.user" :user="session.user" :profile="data.profile" />
        <BadgesSection
          :achievements="data.profile.achievements ?? []"
          :trips="data.trips"
          :entries="data.entries"
          :excursions="data.excursions"
          :routes-completed="data.profile.routes_completed ?? 0"
        />
        <HeroesSection :entries="data.entries" />
      </template>
      <AccountRequired v-else-if="session.isAuthenticated" text="Профиль, роль, герои семьи и значки хранятся в аккаунте" />

      <SettingsSection :profile="data?.profile ?? null" :squads="data?.squads ?? []" @saved="applyProfile" />
      <SupportSection />

      <p class="py-space-sm text-center font-archival text-archival uppercase text-on-surface-variant">
        Сохраняя подвиг защитников Отечества для будущих поколений
      </p>
    </template>

    <ProfileEditSheet
      v-if="editOpen && data"
      :profile="data.profile"
      :fallback-name="session.user?.name ?? ''"
      @saved="applyProfile"
      @close="editOpen = false"
    />
    <ResearcherTokenModal v-if="tokenOpen && session.user" :user="session.user" @close="tokenOpen = false" />
  </div>
</template>
