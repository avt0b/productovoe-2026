import { defineModule } from '@/core/module'

/**
 * Вход и регистрация.
 *
 * Пока заглушка: любой способ входа пускает без проверки. Если модуль убрать,
 * приложение откроется сразу, без экрана входа, — роутер это учитывает.
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
  ],
})
