import { defineModule } from '@/core/module'

/**
 * Центр уведомлений: лента всех событий (не только то, что успело всплыть
 * баннером). Своей вкладки нет — вкладок пять и панель заполнена (см.
 * PLAN-UP-MOBILE.md, §5.4); вход — колокольчик в профиле.
 */
export default defineModule({
  id: 'notifications',
  routes: [
    {
      path: '/notifications',
      name: 'notifications',
      component: () => import('./NotificationsPage.vue'),
      meta: { title: 'Уведомления', layout: 'detail', tab: 'profile' },
    },
  ],
})
