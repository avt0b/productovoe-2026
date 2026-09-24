import { ApiError, apiRequest, ServiceUnavailableError } from '@/core/api'

import { stubAuthProvider } from './stubAuthProvider'
import type { AuthProvider, SessionTokens, SessionUser, SignInRequest, SignInResult, UserRole } from './types'

/**
 * Вход через `auth_service`: почта и пароль, пара JWT-токенов.
 *
 * Демо-вход никуда не делся — без него приложение нельзя показать без
 * сервера. Демо получается, если оставить почту и пароль пустыми. У демо-сессии
 * нет токена, поэтому то, что пишет в сервисы от имени человека (запись на
 * экскурсию, бамп), в ней недоступно.
 *
 * Вход через VK ID, Яндекс ID, MAX и Госуслуги — `externalAuth.ts`: он заканчивается той
 * же парой токенов, её превращает в сессию `fromExternalLogin`.
 */

interface TokenPairDto {
  access_token: string
  refresh_token: string
  token_type: string
  /** Секунд до истечения access-токена. */
  expires_in: number
}

interface UserDto {
  id: string
  email: string
  role: UserRole
  is_root: boolean
  is_active: boolean
  created_at: string
}

const ROLE_TITLES: Record<UserRole, string> = {
  family: 'Участник маршрутов',
  searcher: 'Поисковик',
  local_historian: 'Краевед',
}

/** Имена, введённые при регистрации. В `auth_service` имён нет — профиль появится в `user_service`. */
const NAMES_KEY = 'marshruty.client.names'

function isDemoRequest(request: SignInRequest): boolean {
  return !request.contact?.trim() && !request.password
}

function readNames(): Record<string, string> {
  try {
    return JSON.parse(localStorage.getItem(NAMES_KEY) ?? '{}') as Record<string, string>
  } catch {
    return {}
  }
}

function rememberName(email: string, name: string | undefined): void {
  const trimmed = name?.trim()
  if (!trimmed) return
  try {
    localStorage.setItem(NAMES_KEY, JSON.stringify({ ...readNames(), [email]: trimmed }))
  } catch {
    /* приватный режим — имя возьмём из почты */
  }
}

function toTokens(pair: TokenPairDto): SessionTokens {
  return {
    accessToken: pair.access_token,
    refreshToken: pair.refresh_token,
    expiresAt: Date.now() + pair.expires_in * 1000,
  }
}

function toUser(dto: UserDto): SessionUser {
  return {
    id: dto.id,
    name: readNames()[dto.email] ?? dto.email.split('@')[0],
    headline: ROLE_TITLES[dto.role] ?? ROLE_TITLES.family,
    city: '',
    role: dto.role,
    isRoot: dto.is_root,
    email: dto.email,
  }
}

/** Ответ `/auth/external/complete`: та же пара токенов и имя от провайдера. */
export interface ExternalCompleteDto extends TokenPairDto {
  user: UserDto
  display_name: string
  is_new_user: boolean
}

/** Сессия после входа через VK ID, Яндекс ID, MAX или Госуслуги. Имя берём у провайдера — в auth_service имён нет. */
export function fromExternalLogin(response: ExternalCompleteDto): SignInResult {
  rememberName(response.user.email, response.display_name)
  return { user: toUser(response.user), tokens: toTokens(response) }
}

/** Ошибки сервиса — человеческим языком: сервер не ответил, пароль короткий. */
async function explain<T>(request: () => Promise<T>): Promise<T> {
  try {
    return await request()
  } catch (reason) {
    if (reason instanceof ServiceUnavailableError) {
      throw new Error('Сервер входа не отвечает. Проверьте подключение или оставьте поля пустыми для демо-режима')
    }
    if (reason instanceof ApiError && reason.status === 422) {
      throw new Error('Проверьте почту и пароль: пароль — не короче 8 символов')
    }
    throw reason
  }
}

export const serviceAuthProvider: AuthProvider = {
  async signIn(request) {
    if (isDemoRequest(request)) return stubAuthProvider.signIn(request)

    const email = request.contact?.trim().toLowerCase() ?? ''
    const password = request.password ?? ''
    if (!email.includes('@')) {
      throw new Error('Вход по аккаунту — пока только по почте')
    }

    if (request.method === 'register') {
      if (password.length < 8) throw new Error('Пароль — не короче 8 символов')
      await explain(() =>
        apiRequest('POST', 'auth', '/auth/register', {
          body: { email, password, role: request.role ?? 'family' },
        }),
      )
      rememberName(email, request.name)
    }

    const pair = await explain(() =>
      apiRequest<TokenPairDto>('POST', 'auth', '/auth/login', { body: { email, password } }),
    )
    const tokens = toTokens(pair)
    // Токен ещё не в сессии — передаём его явно.
    const me = await explain(() => apiRequest<UserDto>('GET', 'auth', '/auth/me', { token: tokens.accessToken }))
    return { user: toUser(me), tokens }
  },

  async refresh(tokens) {
    const pair = await apiRequest<TokenPairDto>('POST', 'auth', '/auth/refresh', {
      body: { refresh_token: tokens.refreshToken },
    })
    return toTokens(pair)
  },

  async signOut(tokens) {
    if (!tokens) return
    try {
      await apiRequest('POST', 'auth', '/auth/logout', { body: { refresh_token: tokens.refreshToken } })
    } catch {
      // Сервер не ответил — всё равно выходим локально: человек нажал «Выйти».
    }
  },
}
