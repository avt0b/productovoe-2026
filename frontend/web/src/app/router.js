import { createRouter, createWebHistory } from 'vue-router'
import { routes as victoryRoutes } from '@modules/routes'
import { routes as lastBattleRoutes } from '@modules/last-battle'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [{ path: '/', redirect: '/routes' }, ...victoryRoutes, ...lastBattleRoutes],
})

export default router
