<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { ApiError } from '@/core/api'
import { errorText } from '@/core/format'
import { useSessionStore } from '@/core/session'
import AccountRequired from '@/ui/AccountRequired.vue'
import Mascot from '@/ui/Mascot.vue'
import MsIcon from '@/ui/MsIcon.vue'

import { MOCK, redeemRoleGrant, type RoleGrantResult } from './api'
import RankCeremony from './components/RankCeremony.vue'

type State =
  | { kind: 'checking' }
  | { kind: 'granted'; result: RoleGrantResult }
  | { kind: 'account' }
  | { kind: 'failed'; message: string; retry: boolean }

const route = useRoute()
const router = useRouter()
const session = useSessionStore()

const state = ref<State>({ kind: 'checking' })
const key = computed(() => (typeof route.query.k === 'string' ? route.query.k.trim() : ''))

// Праздник начнётся сразу после ответа сервиса — картинка к этому моменту должна быть в памяти.
new Image().src = '/mascot/celebrate-hd.webp'

/** Номер попытки: вторая метка, приложенная во время проверки первой, отменяет её ответ. */
let attempt = 0

async function redeem(): Promise<void> {
  const current = ++attempt
  const user = session.user
  if (!key.value) {
    state.value = { kind: 'failed', message: 'На метке нет ключа — её записали не той ссылкой', retry: false }
    return
  }
  if (!user || (!session.hasAccount && !MOCK)) {
    state.value = { kind: 'account' }
    return
  }
  state.value = { kind: 'checking' }
  try {
    const result = await redeemRoleGrant({ key: key.value, user_id: user.id, nickname: user.name })
    if (current !== attempt) return
    state.value = { kind: 'granted', result }
    // Новая роль — в сессию, пока идёт праздник: профиль и кнопки перерисуются сами.
    void session.reloadUser()
  } catch (reason) {
    if (current !== attempt) return
    state.value = { kind: 'failed', message: failure(reason), retry: !(reason instanceof ApiError) }
  }
}

/** Ответ сервиса — его же словами; 422 значит, что на метке не ключ, а что-то другое. */
function failure(reason: unknown): string {
  if (reason instanceof ApiError && reason.status === 422) return 'Метка не подходит'
  return errorText(reason)
}

// Ключ меняется, когда поверх открытого экрана приложили другую метку.
watch(key, () => void redeem(), { immediate: true })

/** Туда, откуда пришли; открыли приложение меткой — на главный экран. */
function leave(): void {
  if (window.history.state?.back) router.back()
  else void router.replace({ name: 'home' })
}

function toProfile(): void {
  if (router.hasRoute('profile')) void router.replace({ name: 'profile' })
  else leave()
}
</script>

<template>
  <RankCeremony
    v-if="state.kind === 'granted'"
    :role="state.result.role"
    :name="session.user?.name ?? ''"
    :already="state.result.already"
    @profile="toProfile"
    @close="leave"
  />

  <div v-else class="flex flex-1 flex-col items-center justify-center gap-space-md px-margin py-space-xl text-center" aria-live="polite">
    <template v-if="state.kind === 'checking'">
      <Mascot pose="salute" :size="160" class="animate-pulse" />
      <h1 class="font-headline-lg-mobile text-headline-lg-mobile text-on-surface">Проверяем метку…</h1>
      <p class="font-body-md text-body-md text-on-surface-variant">Пара секунд — и узнаем, какое звание она даёт</p>
    </template>

    <template v-else-if="state.kind === 'account'">
      <Mascot pose="question" :size="140" />
      <h1 class="font-headline-lg-mobile text-headline-lg-mobile text-on-surface">Звание — только аккаунту</h1>
      <AccountRequired class="w-full text-left" text="Войдите своим аккаунтом и приложите метку ещё раз" />
      <button
        type="button"
        class="rounded-full bg-surface-container-high px-space-md py-2 font-label-md text-label-md text-on-surface active:scale-95"
        @click="leave"
      >
        Закрыть
      </button>
    </template>

    <template v-else-if="state.kind === 'failed'">
      <Mascot pose="question" :size="140" />
      <h1 class="font-headline-lg-mobile text-headline-lg-mobile text-on-surface">Не получилось</h1>
      <p class="font-body-md text-body-md text-on-surface-variant">{{ state.message }}</p>
      <button
        v-if="state.retry"
        type="button"
        class="flex w-full items-center justify-center gap-space-sm rounded-xl bg-primary-container py-3.5 font-label-lg text-label-lg uppercase tracking-wide text-white shadow-stamp transition-all hover:bg-primary active:scale-[0.99] short:py-2.5"
        @click="redeem"
      >
        <MsIcon name="refresh" :size="20" />
        Попробовать ещё раз
      </button>
      <button
        type="button"
        class="rounded-full bg-surface-container-high px-space-md py-2 font-label-md text-label-md text-on-surface active:scale-95"
        @click="leave"
      >
        Закрыть
      </button>
    </template>
  </div>
</template>
