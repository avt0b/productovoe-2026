/** Роль в платформе — как в `auth_service`. */
export type UserRole = 'family' | 'searcher' | 'local_historian' | 'mentor' | 'moderator'

/** Пользователь текущей сессии — ровно то, что нужно интерфейсу, без полей бэкенда. */
export interface SessionUser {
  id: string
  name: string
  /** Подпись под именем: «Волонтер-исследователь • Отряд «Высота»». */
  headline: string
  city: string
  avatarUrl?: string
  /** Роль из `auth_service`. У демо-пользователя её нет. */
  role?: UserRole
  /** Администратор платформы (`is_root`): сервисы пускают его туда же, куда модератора. */
  isRoot?: boolean
  email?: string
}

/** Токены `auth_service`. У демо-сессии их нет. */
export interface SessionTokens {
  accessToken: string
  refreshToken: string
  /** Когда истекает access-токен, мс unix-времени. */
  expiresAt: number
}

/**
 * Каким способом человек входит. Пароль и регистрация идут в `auth_service`,
 * Госуслуги / VK ID / Сбер ID пока ведут в демо-вход.
 */
export type SignInMethod = 'password' | 'register' | 'gosuslugi' | 'vk-id' | 'sber-id'

export interface SignInRequest {
  method: SignInMethod
  /** Почта. Пустая вместе с паролем — демо-вход. */
  contact?: string
  password?: string
  /** Имя при регистрации. */
  name?: string
  /** Роль при регистрации: краевед или наставник водит экскурсии. */
  role?: UserRole
}

export interface SignInResult {
  user: SessionUser
  /** `null` — демо-вход без аккаунта. */
  tokens: SessionTokens | null
}

/**
 * Источник сессии. Экраны не знают, откуда берётся пользователь: провайдер
 * выбирается одной строкой в `store.ts`.
 */
export interface AuthProvider {
  signIn(request: SignInRequest): Promise<SignInResult>
  /** Выпустить новую пару токенов по refresh-токену. */
  refresh(tokens: SessionTokens): Promise<SessionTokens>
  signOut(tokens: SessionTokens | null): Promise<void>
}
