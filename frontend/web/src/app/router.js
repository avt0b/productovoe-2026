import { createRouter, createWebHistory } from 'vue-router'
import { routes as victoryRoutes } from '@modules/routes'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [{ path: '/', redirect: '/routes' }, ...victoryRoutes],
})

export default router
