import { defineModule } from '@/core/module'

/** Профиль исследователя: достижения, семейное древо, контакты, настройки, выход. */
export default defineModule({
  id: 'profile',
  tab: { title: 'Профиль', icon: 'account_circle', route: 'profile', order: 50 },
  routes: [
    {
      path: '/profile',
      name: 'profile',
      component: () => import('./ProfilePage.vue'),
      meta: { title: 'Профиль' },
    },
  ],
})
