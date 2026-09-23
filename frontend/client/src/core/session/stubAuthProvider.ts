import { withLatency } from '@/core/mock'

import type { AuthProvider, SessionUser } from './types'

/**
 * Тот, кто зашёл осмотреться без учётной записи.
 *
 * Имя и подпись честно говорят, что это демо: выдуманный «Константин Смирнов
 * из отряда „Высота“» выглядел как чужие настоящие данные. Аватара нет —
 * показывается силуэт.
 */
const DEMO_USER: SessionUser = {
  id: 'demo',
  name: 'Тест',
  headline: 'Демо-режим без учётной записи',
  city: '',
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
