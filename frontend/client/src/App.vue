<script setup lang="ts">
import { computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import BareLayout from '@/app/layouts/BareLayout.vue'
import DetailLayout from '@/app/layouts/DetailLayout.vue'
import TabsLayout from '@/app/layouts/TabsLayout.vue'
import { useSessionStore } from '@/core/session'
import { LostAlertBanner } from '@/features/lost-alert'
import { NotificationBanner } from '@/features/notifications'
import { WelcomeSheet } from '@/features/onboarding'
import { useGrantTags } from '@/features/role-grant'

const route = useRoute()
const router = useRouter()
const session = useSessionStore()

// Метка звания открывает экран выдачи с любого экрана — и когда приложение закрыто.
useGrantTags()

/** Каркас экрана выбирает сам экран через `meta.layout`; по умолчанию — с вкладками. */
const layouts = { tabs: TabsLayout, detail: DetailLayout, bare: BareLayout }
const layout = computed(() => layouts[route.meta.layout ?? 'tabs'])

/**
 * Сессию закрыл сервер — остаться на экране значило бы получать «Сессия
 * истекла» на каждое нажатие. Уводим на вход, запомнив, где человек был.
 */
watch(
  () => session.expired,
  (expired) => {
    if (!expired || route.meta.public || !router.hasRoute('auth')) return
    void router.replace({ name: 'auth', query: { next: route.fullPath } })
  },
)
</script>

<template>
  <component :is="layout">
    <RouterView />
  </component>
  <!-- Поверх любого экрана: сбор начинается, пока человек смотрит карту, а не экскурсию. -->
  <NotificationBanner />
  <!-- Тревога «Я потерялся» важнее любого экрана: плашка в корне вернёт к поиску, где бы человек ни был. -->
  <LostAlertBanner />
  <!-- Первый вход: предложить показать, что где. Один раз и только вошедшим. -->
  <WelcomeSheet />
</template>
