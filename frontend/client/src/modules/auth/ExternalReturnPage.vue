<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { errorText } from '@/core/format'
import { clearPendingLogin, closeExternalBrowser, completeExternalLogin, readPendingLogin, useSessionStore } from '@/core/session'
import MsIcon from '@/ui/MsIcon.vue'

/**
 * Возврат после подтверждения у VK ID или Госуслуг: `/auth/external?result_code=…`
 * (в APK — ссылкой `marshruty://auth/external`). Попытку входа приложение
 * запомнило перед уходом к провайдеру; здесь меняет код на пару токенов.
 */
const route = useRoute()
const router = useRouter()
const session = useSessionStore()

/** Сервис ещё не увидел подтверждения — переспросить через пару секунд, но не бесконечно. */
const RETRY_MS = 2000
const MAX_ATTEMPTS = 10

/**
 * `auth_service` кладёт в `error` готовую фразу («Вход не подтверждён: …»).
 * Коды провайдеров на случай, если придут они, — человеческим языком.
 */
const REASONS: Record<string, string> = {
  access_denied: 'Вы отменили вход у провайдера',
}

const problem = ref<string | null>(null)
let timer: ReturnType<typeof setTimeout> | undefined

function queryValue(name: string): string | null {
  const value = route.query[name]
  return typeof value === 'string' && value ? value : null
}

async function finish(attempt = 1): Promise<void> {
  const pending = readPendingLogin()
  if (!pending) {
    problem.value = 'Попытка входа не найдена или устарела — начните вход заново'
    return
  }
  try {
    const result = await completeExternalLogin(pending, queryValue('result_code'))
    if (!result) {
      if (attempt >= MAX_ATTEMPTS) problem.value = 'Провайдер так и не подтвердил вход — попробуйте ещё раз'
      else timer = setTimeout(() => void finish(attempt + 1), RETRY_MS)
      return
    }
    session.adopt(result)
    await router.replace({ name: 'home' })
  } catch (reason) {
    problem.value = errorText(reason)
  }
}

onMounted(() => {
  closeExternalBrowser()
  const error = queryValue('error')
  if (error) {
    problem.value = REASONS[error] ?? error
    clearPendingLogin()
  } else void finish()
})

onBeforeUnmount(() => clearTimeout(timer))

async function backToSignIn(): Promise<void> {
  // Демо-сессия охраной роутера не пустила бы на экран входа.
  if (session.isAuthenticated) await session.signOut()
  await router.replace(router.hasRoute('auth') ? { name: 'auth' } : { name: 'home' })
}
</script>

<template>
  <div class="flex min-h-screen w-full flex-col items-center justify-center gap-space-md px-margin text-center">
    <template v-if="!problem">
      <MsIcon name="progress_activity" :size="40" class="animate-spin text-primary" />
      <p class="font-headline-sm text-headline-sm text-on-surface">Входим в аккаунт…</p>
    </template>
    <template v-else>
      <MsIcon name="error" :size="40" class="text-error" />
      <p class="font-headline-sm text-headline-sm text-on-surface">{{ problem }}</p>
      <button
        type="button"
        class="rounded-full bg-primary px-space-lg py-3 font-label-lg text-label-lg text-on-primary shadow-md active:scale-95"
        @click="backToSignIn"
      >
        Вернуться ко входу
      </button>
    </template>
  </div>
</template>
