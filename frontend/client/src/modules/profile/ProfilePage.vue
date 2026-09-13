<script setup lang="ts">
import { ref } from 'vue'

import { useAsync } from '@/core/async'
import { useSessionStore } from '@/core/session'
import StateBlock from '@/ui/StateBlock.vue'

import AncestorsSection from './components/AncestorsSection.vue'
import BadgesSection from './components/BadgesSection.vue'
import ContactsSection from './components/ContactsSection.vue'
import ExpeditionStatusCard from './components/ExpeditionStatusCard.vue'
import ResearcherHeroCard from './components/ResearcherHeroCard.vue'
import ResearcherTokenModal from './components/ResearcherTokenModal.vue'
import SettingsSection from './components/SettingsSection.vue'
import SupportSection from './components/SupportSection.vue'
import { fetchProfile } from './data'

const session = useSessionStore()
const { data, loading, error, retry } = useAsync(fetchProfile)

const tokenOpen = ref(false)
</script>

<template>
  <div class="flex w-full flex-col gap-space-md px-margin pb-6">
    <div class="flex items-center justify-between rounded-full bg-surface-container-low px-space-md py-space-sm shadow-sm">
      <div class="flex items-center gap-space-xs">
        <span class="h-2.5 w-2.5 animate-pulse rounded-full bg-secondary" />
        <span class="font-label-sm text-label-sm uppercase tracking-wide text-secondary">Полевой штаб активен</span>
      </div>
      <span v-if="session.user" class="font-label-sm text-label-sm font-bold tracking-wider text-outline">
        ID: #{{ session.user.id }}
      </span>
    </div>

    <StateBlock v-if="loading || error" :loading="loading" :error="error" @retry="retry" />

    <template v-else-if="data">
      <ResearcherHeroCard
        :user="session.user"
        :experience="data.experience"
        :counters="data.counters"
        @open-token="tokenOpen = true"
      />
      <ExpeditionStatusCard v-bind="data.expedition" />
      <AncestorsSection :ancestors="data.ancestors" />
      <BadgesSection :badges="data.badges" :total="data.badgesTotal" />
      <ContactsSection :contacts="data.contacts" />
      <SettingsSection :settings="data.settings" />
      <SupportSection :curator="data.curator" />

      <div class="flex flex-col items-center gap-0.5 py-2 text-center">
        <span class="font-label-sm text-label-sm text-outline">{{ data.version }}</span>
        <span class="font-body-sm text-label-sm font-normal text-outline">
          Сохраняя подвиг защитников Отечества для будущих поколений
        </span>
      </div>
    </template>

    <ResearcherTokenModal v-if="tokenOpen && session.user" :user="session.user" @close="tokenOpen = false" />
  </div>
</template>
