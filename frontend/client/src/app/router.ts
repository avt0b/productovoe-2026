import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'

import { useSessionStore } from '@/core/session'

import { modules, tabs } from './registry'

const moduleRoutes = modules.flatMap((module) => module.routes)

/** Экран входа — если модуль входа подключён. Нет его — приложение открыто всем. */
const authRouteName = moduleRoutes.find((route) => route.meta?.auth)?.name

/** Первая вкладка — стартовый экран. */
const homeRouteName = tabs[0]?.route

const routes: RouteRecordRaw[] = [
  ...moduleRoutes,
  {
    path: '/',
    name: 'home',
    redirect: () => (homeRouteName ? { name: homeRouteName } : { name: 'no-modules' }),
  },
  {
    path: '/no-modules',
    name: 'no-modules',
    component: () => import('./pages/NoModulesPage.vue'),
    meta: { layout: 'bare', public: true },
  },
  { path: '/:pathMatch(.*)*', redirect: { name: 'home' } },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  // Назад — на прежнюю позицию прокрутки, на новый экран — в начало.
  scrollBehavior: (_to, _from, saved) => saved ?? { top: 0 },
})

router.beforeEach((to) => {
  if (!authRouteName) return true

  const session = useSessionStore()

  if (to.meta.auth) {
    return session.isAuthenticated ? { name: 'home' } : true
  }
  if (to.meta.public || session.isAuthenticated) {
    return true
  }
  return {
    name: authRouteName,
    query: to.fullPath === '/' ? undefined : { next: to.fullPath },
  }
})

export default router
