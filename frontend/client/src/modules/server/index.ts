import { defineModule } from '@/core/module'

/**
 * «Сервер»: к какому бэкенду подключается приложение.
 *
 * Временный модуль на время тестов — пока сервисы поднимают на своих
 * компьютерах. Убрать — удалить папку: экран входа перестанет показывать
 * строку «Сервер», приложение пойдёт по адресам из сборки (`.env.local`).
 */
export default defineModule({
  id: 'server',
  routes: [
    {
      path: '/server',
      name: 'server',
      component: () => import('./ServerPage.vue'),
      meta: { title: 'Сервер', layout: 'detail', public: true },
    },
  ],
})
