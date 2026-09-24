/**
 * Роль в платформе — как в `auth_service`. Ролей три; четвёртая по продукту,
 * администратор, — не роль, а флаг `is_root` (см. `SessionUser.isRoot`).
 */
export type UserRole = 'family' | 'searcher' | 'local_historian'

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
  /** Администратор платформы (`is_root`): стафф-права сервисов остались только у него. */
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
 * Вход по паролю или регистрация в `auth_service`. VK ID, MAX и Госуслуги —
 * отдельный путь через провайдера (`externalAuth.ts`).
 */
export type SignInMethod = 'password' | 'register'

export interface SignInRequest {
  method: SignInMethod
  /** Почта. Пустая вместе с паролем — демо-вход. */
  contact?: string
  password?: string
  /** Имя при регистрации. */
  name?: string
  /**
   * Роль при регистрации. `auth_service` принимает только «семью»
   * (`SELF_ASSIGNABLE_ROLES`), поисковиком и краеведом становятся по заявке.
   */
  role?: 'family'
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
