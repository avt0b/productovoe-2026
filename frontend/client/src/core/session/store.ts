import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import { setAuthHandlers } from '@/core/api'

import { serviceAuthProvider } from './serviceAuthProvider'
import type { AuthProvider, SessionTokens, SessionUser, SignInRequest } from './types'

/** Источник сессии. Здесь, и только здесь, выбирается, откуда берётся вход. */
const provider: AuthProvider = serviceAuthProvider

const STORAGE_KEY = 'marshruty.client.session'

interface StoredSession {
  user: SessionUser
  tokens: SessionTokens | null
}

/**
 * Сессия живёт в localStorage: перезагрузка страницы не должна выкидывать на вход.
 *
 * Токены там же — это прототип. В проде refresh-токен хранят в защищённом
 * хранилище телефона (Android Keystore), а не в localStorage WebView.
 */
function readStored(): StoredSession | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return null
    const parsed = JSON.parse(raw) as StoredSession | SessionUser
    // Раньше хранился голый пользователь демо-входа — такую сессию не теряем.
    return 'user' in parsed ? parsed : { user: parsed, tokens: null }
  } catch {
    return null
  }
}

function writeStored(session: StoredSession | null): void {
  try {
    if (session) localStorage.setItem(STORAGE_KEY, JSON.stringify(session))
    else localStorage.removeItem(STORAGE_KEY)
  } catch {
    /* приватный режим — сессия проживёт до закрытия вкладки */
  }
}

export const useSessionStore = defineStore('session', () => {
  const stored = readStored()
  const user = ref<SessionUser | null>(stored?.user ?? null)
  const tokens = ref<SessionTokens | null>(stored?.tokens ?? null)
  const pending = ref(false)

  const isAuthenticated = computed(() => user.value !== null)
  /**
   * Вошёл настоящим аккаунтом, а не в демо. Только так работает то, что пишет
   * в сервисы от имени человека: запись на экскурсию, бамп.
   */
  const hasAccount = computed(() => tokens.value !== null)

  function persist(): void {
    writeStored(user.value ? { user: user.value, tokens: tokens.value } : null)
  }

  async function signIn(request: SignInRequest): Promise<void> {
    pending.value = true
    try {
      const result = await provider.signIn(request)
      user.value = result.user
      tokens.value = result.tokens
      persist()
    } finally {
      pending.value = false
    }
  }

  let refreshing: Promise<boolean> | null = null

  /** Обновить токены. Несколько запросов, упавших с 401 одновременно, делят одно обновление. */
  function refresh(): Promise<boolean> {
    const current = tokens.value
    if (!current) return Promise.resolve(false)
    refreshing ??= provider
      .refresh(current)
      .then((next) => {
        tokens.value = next
        persist()
        return true
      })
      .catch(() => false)
      .finally(() => {
        refreshing = null
      })
    return refreshing
  }

  async function signOut(): Promise<void> {
    pending.value = true
    try {
      await provider.signOut(tokens.value)
    } finally {
      // Выходим локально, даже если сервер не ответил: человек нажал «Выйти».
      user.value = null
      tokens.value = null
      writeStored(null)
      pending.value = false
    }
  }

  /**
   * Уточнить пользователя сессии: имя и город приходят из профиля
   * (`user_service`), а не из входа — в `auth_service` их нет.
   */
  function updateUser(patch: Partial<Pick<SessionUser, 'name' | 'city' | 'headline' | 'avatarUrl'>>): void {
    if (!user.value) return
    user.value = { ...user.value, ...patch }
    persist()
  }

  setAuthHandlers({ accessToken: () => tokens.value?.accessToken ?? null, refresh })

  return { user, tokens, pending, isAuthenticated, hasAccount, signIn, signOut, refresh, updateUser }
})
