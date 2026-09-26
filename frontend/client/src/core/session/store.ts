import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import { ApiError, setAuthHandlers } from '@/core/api'

import { serviceAuthProvider } from './serviceAuthProvider'
import type { AuthProvider, SessionTokens, SessionUser, SignInRequest, SignInResult } from './types'

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
  /** Сессию закрыл сервер, а не человек: каркас приложения уводит на вход. */
  const expired = ref(false)

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
      expired.value = false
      persist()
    } finally {
      pending.value = false
    }
  }

  /** Принять готовую сессию — после входа через VK ID, Яндекс ID, MAX или Госуслуги. */
  function adopt(result: SignInResult): void {
    user.value = result.user
    tokens.value = result.tokens
    expired.value = false
    persist()
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
      .catch((reason) => {
        // Сервис входа отверг refresh-токен (отозван, истёк, база стенда
        // пересоздана) — сессия мертва, и каждый запрос дальше получал бы 401.
        // Нет сети — другое дело: токены ещё пригодятся, человека не выкидываем.
        if (reason instanceof ApiError && reason.status < 500) expire()
        return false
      })
      .finally(() => {
        refreshing = null
      })
    return refreshing
  }

  /**
   * Перечитать пользователя с сервера: роль сменилась без перевхода (NFC-метка).
   *
   * Роль зашита в access-токен, поэтому сначала новый токен — без него
   * сервисы до его истечения отвечали бы по старой роли. Имя, город и фото
   * приходят из профиля (`updateUser`), их не трогаем.
   */
  async function reloadUser(): Promise<boolean> {
    if (!(await refresh()) || !tokens.value) return false
    try {
      const fresh = await provider.currentUser(tokens.value)
      if (!user.value) return false
      user.value = { ...user.value, role: fresh.role, isRoot: fresh.isRoot, headline: fresh.headline }
      persist()
      return true
    } catch {
      // Нет сети — роль догонит при следующем обновлении токена.
      return false
    }
  }

  function expire(): void {
    user.value = null
    tokens.value = null
    expired.value = true
    writeStored(null)
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

  setAuthHandlers({
    accessToken: () => tokens.value?.accessToken ?? null,
    expiresAt: () => tokens.value?.expiresAt ?? null,
    refresh,
  })

  return {
    user,
    tokens,
    pending,
    expired,
    isAuthenticated,
    hasAccount,
    signIn,
    adopt,
    signOut,
    refresh,
    reloadUser,
    updateUser,
  }
})
