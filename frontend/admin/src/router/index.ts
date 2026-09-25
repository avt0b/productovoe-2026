import { createRouter, createWebHistory } from 'vue-router'

import { useAuthStore } from '@/stores/auth'

/**
 * Пункты меню объявлены прямо в роутах (`meta.nav`), чтобы боковая панель
 * строилась из одного источника и не разъезжалась с реальными маршрутами.
 */
export interface NavMeta {
  title: string
  icon: string
  group: 'main' | 'system'
}

declare module 'vue-router' {
  interface RouteMeta {
    public?: boolean
    superadmin?: boolean
    nav?: NavMeta
  }
}

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginView.vue'),
      meta: { public: true },
    },
    {
      path: '/setup-2fa',
      name: 'totp-setup',
      component: () => import('@/views/TotpSetupView.vue'),
    },
    {
      path: '/',
      name: 'dashboard',
      component: () => import('@/views/DashboardView.vue'),
      meta: { nav: { title: 'Обзор', icon: 'dashboard', group: 'main' } },
    },
    {
      path: '/users',
      name: 'users',
      component: () => import('@/views/UsersView.vue'),
      meta: { nav: { title: 'Пользователи и роли', icon: 'group', group: 'main' } },
    },
    {
      path: '/moderation',
      name: 'moderation',
      component: () => import('@/views/ModerationView.vue'),
      meta: { nav: { title: 'Модерация заявок', icon: 'rate_review', group: 'main' } },
    },
    {
      path: '/last-stand',
      name: 'last-stand',
      component: () => import('@/views/LastStandView.vue'),
      meta: { nav: { title: 'Точки «Последнего боя»', icon: 'pin_drop', group: 'main' } },
    },
    {
      path: '/search-hq',
      name: 'search-hq',
      component: () => import('@/views/SearchHqView.vue'),
      meta: { nav: { title: 'Отряды и сборы', icon: 'travel_explore', group: 'main' } },
    },
    {
      path: '/routes',
      name: 'routes',
      component: () => import('@/views/RoutesView.vue'),
      meta: { nav: { title: 'Маршруты', icon: 'route', group: 'main' } },
    },
    {
      path: '/clips',
      name: 'clips',
      component: () => import('@/views/ClipsView.vue'),
      meta: { nav: { title: '«Живое фото»', icon: 'photo_camera_front', group: 'main' } },
    },
    {
      path: '/audit',
      name: 'audit',
      component: () => import('@/views/AuditView.vue'),
      meta: { nav: { title: 'Журнал аудита', icon: 'history', group: 'system' } },
    },
    {
      path: '/accounts',
      name: 'accounts',
      component: () => import('@/views/AccountsView.vue'),
      meta: {
        superadmin: true,
        nav: { title: 'Администраторы', icon: 'admin_panel_settings', group: 'system' },
      },
    },
    {
      path: '/security',
      name: 'security',
      component: () => import('@/views/SecurityView.vue'),
      meta: { nav: { title: 'Моя безопасность', icon: 'security', group: 'system' } },
    },
    { path: '/:pathMatch(.*)*', redirect: { name: 'dashboard' } },
  ],
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()
  await auth.bootstrap()

  if (to.meta.public) {
    return auth.isAuthenticated ? { name: 'dashboard' } : true
  }

  if (!auth.isAuthenticated) {
    return { name: 'login', query: to.fullPath === '/' ? undefined : { next: to.fullPath } }
  }

  // Пока TOTP не настроен, бэкенд всё равно отвечает 403 — не водим по пустым экранам.
  if (auth.needsTotpSetup && to.name !== 'totp-setup') {
    return { name: 'totp-setup' }
  }
  // Настроить второй фактор можно и добровольно (кнопка в «Моей безопасности»),
  // поэтому закрываем экран только когда настраивать уже нечего.
  if (to.name === 'totp-setup' && auth.me?.totp_enabled) {
    return { name: 'dashboard' }
  }

  if (to.meta.superadmin && !auth.isSuperadmin) {
    return { name: 'dashboard' }
  }

  return true
})

export default router
