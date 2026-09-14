/** Пользователь текущей сессии — ровно то, что нужно интерфейсу, без полей бэкенда. */
export interface SessionUser {
  id: string
  name: string
  /** Подпись под именем: «Волонтер-исследователь • Отряд «Высота»». */
  headline: string
  city: string
  avatarUrl?: string
}

/** Каким способом человек входит. Пока все способы ведут в одну заглушку. */
export type SignInMethod = 'password' | 'register' | 'gosuslugi' | 'vk-id' | 'sber-id'

export interface SignInRequest {
  method: SignInMethod
  /** Телефон или почта. Заглушка его не проверяет. */
  contact?: string
  password?: string
  /** Имя при регистрации. */
  name?: string
}

/**
 * Источник сессии. Экраны не знают, откуда берётся пользователь: сейчас это
 * заглушка, потом — `auth_service`. Замена — одна строка в `store.ts`.
 */
export interface AuthProvider {
  signIn(request: SignInRequest): Promise<SessionUser>
  signOut(): Promise<void>
}
