<script setup lang="ts">
import { computed, ref } from 'vue'

import { useAsync } from '@/core/async'
import { useSessionStore } from '@/core/session'
import StateBlock from '@/ui/StateBlock.vue'

import BadgesSection from './components/BadgesSection.vue'
import ResearcherHeroCard from './components/ResearcherHeroCard.vue'
import ProfileEditModal from './components/ProfileEditModal.vue'
import SignOutSection from './components/SignOutSection.vue'
import type { Profile } from './api'
import { loadProfile } from './data'

const session = useSessionStore()
const { data, loading, error, retry } = useAsync(loadProfile)

const editing = ref(false)

/** Сохранённый профиль приходит в ответе PUT — перезапрашивать экран незачем. */
function onSaved(profile: Profile): void {
  if (data.value) data.value = { ...data.value, profile }
  editing.value = false
}

/**
 * Демо-вход идёт без токенов, а `user_service` отдаёт профиль только своему
 * владельцу. Отличает их `hasAccount`, а не `isAuthenticated`: последний
 * истинен и в демо — человек в приложении, просто без учётной записи.
 * Показывать ему ошибку «нужно войти по почте» неправильно, он ничего не сломал.
 */
const demoMode = computed(() => !session.hasAccount)
</script>

<template>
  <div class="flex w-full flex-col gap-space-md pb-6">
    <p
      v-if="demoMode"
      class="mx-margin rounded-DEFAULT bg-surface-container-lowest p-space-md font-body-sm text-body-sm text-on-surface-variant shadow-sm"
    >
      Вы в демо-режиме: профиль исследователя хранится в учётной записи. Войдите по почте, чтобы он появился здесь.
    </p>

    <template v-else>
      <StateBlock v-if="loading || error" class="mx-margin" :loading="loading" :error="error" @retry="retry" />

      <template v-else-if="data">
        <!--
          Карточка идёт от края до края и вплотную к верхней кромке: она не
          отдельный блок на листе, а шапка экрана. `-mt` съедает верхний отступ
          каркаса вкладок, оставляя отступ под системную полосу.
        -->
        <ResearcherHeroCard
          class="-mt-space-md rounded-b-lg"
          :profile="data.profile"
          :email="session.user?.email"
          @edit="editing = true"
        />
        <BadgesSection class="mx-margin" :achievements="data.achievements" />
      </template>
    </template>

    <SignOutSection class="mx-margin" />

    <ProfileEditModal v-if="editing && data" :profile="data.profile" @close="editing = false" @saved="onSaved" />
  </div>
</template>
