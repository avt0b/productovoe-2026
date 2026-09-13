import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import { stubAuthProvider } from './stubAuthProvider'
import type { AuthProvider, SessionUser, SignInRequest } from './types'

/** Источник сессии. Здесь, и только здесь, заглушка меняется на настоящий вход. */
const provider: AuthProvider = stubAuthProvider

const STORAGE_KEY = 'marshruty.client.session'

/** Сессия живёт в localStorage: перезагрузка страницы не должна выкидывать на вход. */
function readStored(): SessionUser | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? (JSON.parse(raw) as SessionUser) : null
  } catch {
    return null
  }
}

function writeStored(user: SessionUser | null): void {
  try {
    if (user) localStorage.setItem(STORAGE_KEY, JSON.stringify(user))
    else localStorage.removeItem(STORAGE_KEY)
  } catch {
    /* приватный режим — сессия проживёт до закрытия вкладки */
  }
}

export const useSessionStore = defineStore('session', () => {
  const user = ref<SessionUser | null>(readStored())
  const pending = ref(false)

  const isAuthenticated = computed(() => user.value !== null)

  async function signIn(request: SignInRequest): Promise<void> {
    pending.value = true
    try {
      user.value = await provider.signIn(request)
      writeStored(user.value)
    } finally {
      pending.value = false
    }
  }

  async function signOut(): Promise<void> {
    pending.value = true
    try {
      await provider.signOut()
    } finally {
      // Выходим локально, даже если сервер не ответил: человек нажал «Выйти».
      user.value = null
      writeStored(null)
      pending.value = false
    }
  }

  return { user, pending, isAuthenticated, signIn, signOut }
})
