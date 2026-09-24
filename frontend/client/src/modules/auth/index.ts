import { defineModule } from '@/core/module'

/**
 * Вход и регистрация: почта и пароль, VK ID, Яндекс ID, MAX, Госуслуги (`auth_service`).
 * Демо-вход без аккаунта — пустые поля. Если модуль убрать, приложение
 * откроется сразу, без экрана входа, — роутер это учитывает.
 */
export default defineModule({
  id: 'auth',
  routes: [
    {
      path: '/auth',
      name: 'auth',
      component: () => import('./AuthPage.vue'),
      meta: { title: 'Вход', layout: 'bare', auth: true, public: true },
    },
    {
      // Сюда провайдер возвращает человека после подтверждения. Не `auth`:
      // охрана увела бы с него того, кто уже вошёл в демо-режиме.
      path: '/auth/external',
      name: 'auth-external',
      component: () => import('./ExternalReturnPage.vue'),
      meta: { title: 'Вход', layout: 'bare', public: true },
    },
  ],
})
