<script setup lang="ts">
import { computed, ref, watch } from 'vue'

import { useAsync } from '@/core/async'
import { useSessionStore } from '@/core/session'
import AccountRequired from '@/ui/AccountRequired.vue'
import StateBlock from '@/ui/StateBlock.vue'

import AccountSection from './components/AccountSection.vue'
import BadgesSection from './components/BadgesSection.vue'
import ExpeditionStatusCard from './components/ExpeditionStatusCard.vue'
import HeroesSection from './components/HeroesSection.vue'
import ProfileForm from './components/ProfileForm.vue'
import ResearcherHeroCard from './components/ResearcherHeroCard.vue'
import ResearcherTokenModal from './components/ResearcherTokenModal.vue'
import SettingsSection from './components/SettingsSection.vue'
import SupportSection from './components/SupportSection.vue'
import { fetchProfile, nextTrip, type HeroCounter, type Profile, type ProfileOverview } from './data'

const session = useSessionStore()

/** Демо-режим без аккаунта: профиля в `user_service` нет, показываем гостя и семейный режим. */
const overview = useAsync<ProfileOverview | null>(() => (session.hasAccount ? fetchProfile() : Promise.resolve(null)))
const { data, loading, error, retry } = overview

const tokenOpen = ref(false)

/** Имя и город приходят из профиля — сессия их узнаёт, чтобы шапка и аватар показывали то же. */
function applyProfile(profile: Profile): void {
  if (data.value) data.value = { ...data.value, profile }
  session.updateUser({
    ...(profile.display_name ? { name: profile.display_name } : {}),
    city: profile.city,
  })
}

watch(
  () => data.value?.profile,
  (profile) => {
    if (profile) applyProfile(profile)
  },
)

const counters = computed<HeroCounter[]>(() => [
  { value: data.value?.trips?.length ?? null, label: 'выездов с отрядом' },
  { value: data.value?.entries?.length ?? null, label: 'записей в архиве' },
  { value: data.value?.excursions ?? null, label: 'экскурсий', accent: true },
])
</script>

<template>
  <div class="flex w-full flex-col gap-space-md px-margin pb-6">
    <StateBlock v-if="loading || error" :loading="loading" :error="error" @retry="retry" />

    <template v-else>
      <ResearcherHeroCard
        :user="session.user"
        :verified="data?.profile.is_verified ?? false"
        :since="data?.profile.created_at ?? null"
        :counters="counters"
        @open-token="tokenOpen = true"
      />

      <template v-if="data">
        <ExpeditionStatusCard :trip="nextTrip(data.trips)" />
        <ProfileForm :profile="data.profile" :fallback-name="session.user?.name ?? ''" @saved="applyProfile" />
        <HeroesSection :entries="data.entries" />
        <BadgesSection :trips="data.trips" :entries="data.entries" :excursions="data.excursions" />
      </template>
      <AccountRequired v-else-if="session.isAuthenticated" text="Профиль, герои семьи и значки хранятся в аккаунте" />

      <SettingsSection :profile="data?.profile ?? null" :squads="data?.squads ?? []" @saved="applyProfile" />
      <AccountSection v-if="session.user" :user="session.user" />
      <SupportSection />

      <p class="py-2 text-center font-body-sm text-label-sm font-normal text-outline">
        Сохраняя подвиг защитников Отечества для будущих поколений
      </p>
    </template>

    <ResearcherTokenModal v-if="tokenOpen && session.user" :user="session.user" @close="tokenOpen = false" />
  </div>
</template>
