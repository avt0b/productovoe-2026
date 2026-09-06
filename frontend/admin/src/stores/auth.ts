import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import { clearTokens, getRefreshToken, hasSession, setTokens } from '@/api/client'
import { authApi } from '@/api/endpoints'
import type { MeResponse } from '@/api/types'

/** Роли, которым разрешено что-либо менять. `viewer` только смотрит. */
const WRITE_ROLES = ['superadmin', 'admin', 'moderator']

export const useAuthStore = defineStore('auth', () => {
  const me = ref<MeResponse | null>(null)
  const loading = ref(false)
  const ready = ref(false)

  /** Промежуточное состояние между «пароль принят» и «код введён». */
  const mfaToken = ref<string | null>(null)
  const mfaExpiresIn = ref<number | null>(null)

  const isAuthenticated = computed(() => me.value !== null)
  const isSuperadmin = computed(() => me.value?.role === 'superadmin')
  const canWrite = computed(() => (me.value ? WRITE_ROLES.includes(me.value.role) : false))

  /**
   * Политика требует TOTP, но администратор его ещё не настроил — до
   * настройки бэкенд не пустит никуда, кроме /admin/auth/*.
   */
  const needsTotpSetup = computed(
    () => me.value !== null && me.value.totp_required_by_policy && !me.value.totp_enabled,
  )

  async function fetchMe(): Promise<void> {
    me.value = await authApi.me()
  }

  /** Восстановление сессии при загрузке страницы. */
  async function bootstrap(): Promise<void> {
    if (ready.value) return
    if (hasSession()) {
      try {
        await fetchMe()
      } catch {
        clearTokens()
        me.value = null
      }
    }
    ready.value = true
  }

  /** Шаг 1. Возвращает true, если нужен код второго фактора. */
  async function login(email: string, password: string): Promise<boolean> {
    loading.value = true
    try {
      const result = await authApi.login(email, password)
      if (result.mfa_required) {
        mfaToken.value = result.mfa_token
        mfaExpiresIn.value = result.mfa_expires_in
        return true
      }
      setTokens(result.access_token ?? '', result.refresh_token ?? '')
      await fetchMe()
      return false
    } finally {
      loading.value = false
    }
  }

  /** Шаг 2. Принимает код из приложения либо код восстановления. */
  async function submitMfa(code: string): Promise<void> {
    if (!mfaToken.value) throw new Error('Сессия подтверждения истекла — войдите заново')
    loading.value = true
    try {
      const pair = await authApi.loginMfa(mfaToken.value, code)
      setTokens(pair.access_token, pair.refresh_token)
      mfaToken.value = null
      mfaExpiresIn.value = null
      await fetchMe()
    } finally {
      loading.value = false
    }
  }

  function cancelMfa(): void {
    mfaToken.value = null
    mfaExpiresIn.value = null
  }

  async function logout(): Promise<void> {
    const token = getRefreshToken()
    if (token) {
      try {
        await authApi.logout(token)
      } catch {
        /* сервер мог уже погасить сессию — выходим в любом случае */
      }
    }
    clearTokens()
    me.value = null
    cancelMfa()
  }

  /** Сессию мог погасить сам сервер (смена пароля, отключение учётки). */
  function dropSession(): void {
    clearTokens()
    me.value = null
    cancelMfa()
  }

  return {
    me,
    loading,
    ready,
    mfaToken,
    mfaExpiresIn,
    isAuthenticated,
    isSuperadmin,
    canWrite,
    needsTotpSetup,
    fetchMe,
    bootstrap,
    login,
    submitMfa,
    cancelMfa,
    logout,
    dropSession,
  }
})
