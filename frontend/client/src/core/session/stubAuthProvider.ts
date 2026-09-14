import { withLatency } from '@/core/mock'

import type { AuthProvider, SessionUser } from './types'

/** Демо-исследователь из макета профиля. */
const DEMO_USER: SessionUser = {
  id: 'MP-84920',
  name: 'Константин Смирнов',
  headline: 'Волонтер-исследователь • Отряд «Высота»',
  city: 'г. Орёл',
  avatarUrl:
    'https://lh3.googleusercontent.com/aida-public/AB6AXuDV9_gqL9ecHjRz29Dj4SSQ535RUFfZasr-q0dw7hF6zSx1gWA87IOqCMWwB4IlJameflSYk9WA1NWr0leTOZk6dGJEVSx-ZDnyn1w38eTDjHSbI8bRfeMqRhKYZ70yDZXqrnm7iJSaaPb2oB9oIQaSztAGxZhgLTgXuaxfbnUyupuruyMxqnZrjynEbGONb-N4EmSRl3zZwR2HcmrHrUr-fEhV0AJNW2_f6XE9znZs07HpTSoWCzOB',
}

/**
 * Демо-вход без аккаунта и без проверки учётных данных.
 *
 * Пускает демо-пользователем, токенов не выдаёт. При регистрации подставляется
 * введённое имя, чтобы было видно, что форма вообще что-то передаёт.
 */
export const stubAuthProvider: AuthProvider = {
  async signIn(request) {
    const name = request.name?.trim()
    return withLatency({ user: { ...DEMO_USER, name: name || DEMO_USER.name }, tokens: null })
  },

  async refresh() {
    throw new Error('У демо-сессии нет токена')
  },

  async signOut() {
    await withLatency(undefined)
  },
}
