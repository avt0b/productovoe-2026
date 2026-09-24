<script setup>
import { computed, onMounted, watch } from 'vue'
import ProfileHero from './components/ProfileHero.vue'
import FamilyTree from './components/FamilyTree.vue'
import AwardsBadges from './components/AwardsBadges.vue'
import ResearcherDataForm from './components/ResearcherDataForm.vue'
import LocalHistorianVerification from './components/LocalHistorianVerification.vue'
import { useAuthSession, roleLabel } from '@modules/auth'
import { MyExcursions } from '@modules/excursions'
import { useProfileStore } from './profileStore.js'

const { session } = useAuthSession()
const { profile, loadMyProfile } = useProfileStore()

onMounted(() => {
  if (session.status === 'authenticated') loadMyProfile()
})
watch(
  () => session.status,
  (status) => {
    if (status === 'authenticated') loadMyProfile()
  },
)

// user_service ещё не хранит семейное древо — оно остаётся демо-данными
// компонента (помечено как демо внутри самого компонента). Всё остальное в
// шапке — реальные поля ProfileOut: is_verified/created_at (user_service),
// routes_completed/excursions_completed/finds_count (заполняются через
// stats_service). Пока profile.data не загружен, heroProps пуст —
// ProfileHero сам показывает нейтральные заглушки, а не чьё-то чужое имя.
const heroProps = computed(() => {
  if (!profile.data) return {}
  return {
    name: profile.data.display_name || session.user?.email || 'Без имени',
    role: roleLabel(profile.data.role),
    city: profile.data.city || '',
    avatarUrl: profile.data.avatar_url || '',
    verified: profile.data.is_verified,
    since: profile.data.created_at,
    routesCompleted: profile.data.routes_completed,
    excursionsCompleted: profile.data.excursions_completed,
    findsCount: profile.data.finds_count,
  }
})
</script>

<template>
  <div class="flex flex-col w-full pb-16">
    <p
      v-if="session.status !== 'authenticated'"
      class="mb-4 px-4 py-3 rounded-DEFAULT bg-surface-container-low text-on-surface-variant font-body-sm text-body-sm"
    >
      Показан демо-профиль. <RouterLink to="/auth" class="text-primary font-bold hover:underline">Войдите</RouterLink>,
      чтобы видеть и редактировать свои настоящие данные (user_service).
    </p>

    <ProfileHero v-bind="heroProps" />

    <div class="grid grid-cols-1 lg:grid-cols-12 gap-8">
      <div class="lg:col-span-7 flex flex-col gap-8">
        <FamilyTree />
        <AwardsBadges />
      </div>

      <div class="lg:col-span-5 flex flex-col gap-8">
        <MyExcursions />
        <LocalHistorianVerification />
        <ResearcherDataForm />
      </div>
    </div>
  </div>
</template>
