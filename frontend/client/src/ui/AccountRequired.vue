<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { useSessionStore } from '@/core/session'

import MsIcon from './MsIcon.vue'

/**
 * «Нужен аккаунт»: то, что пишет в сервисы от имени человека (взнос, запись,
 * новая точка), в демо-режиме без аккаунта недоступно.
 */
defineProps<{ text: string }>()

const route = useRoute()
const router = useRouter()
const session = useSessionStore()

/** Экран входа — отдельный модуль. Нет его — просто объясняем, без кнопки. */
const canSignIn = computed(() => router.hasRoute('auth'))

/** Из демо-сессии на экран входа: охрана роутера пускает туда только тех, кто не вошёл. */
async function signIn(): Promise<void> {
  await session.signOut()
  await router.push({ name: 'auth', query: { next: route.fullPath } })
}
</script>

<template>
  <div class="flex items-start gap-space-sm rounded-lg bg-tertiary-fixed/40 p-space-md">
    <div class="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-tertiary-fixed text-on-tertiary-fixed-variant">
      <MsIcon name="lock" :size="20" />
    </div>
    <div class="min-w-0 flex-1">
      <p class="font-label-lg text-label-lg text-on-surface">{{ text }}</p>
      <p class="mt-0.5 font-body-sm text-body-sm text-on-surface-variant">Сейчас вы в демо-режиме без аккаунта.</p>
      <button
        v-if="canSignIn"
        type="button"
        class="mt-space-sm inline-flex items-center gap-1.5 rounded-full bg-tertiary px-space-md py-2 font-label-md text-label-md text-on-tertiary active:scale-95"
        :disabled="session.pending"
        @click="signIn"
      >
        <MsIcon name="login" :size="18" />
        Войти в аккаунт
      </button>
    </div>
  </div>
</template>
