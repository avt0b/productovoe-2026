import { createRouter, createWebHistory } from 'vue-router'
import { routes as victoryRoutes } from '@modules/routes'
import { routes as lastBattleRoutes } from '@modules/last-battle'
import { routes as expeditionHqRoutes } from '@modules/expedition-hq'
import { routes as fundraisingRoutes } from '@modules/fundraising'
import { routes as livingMemoryRoutes } from '@modules/living-memory'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/', redirect: '/routes' },
    ...victoryRoutes,
    ...lastBattleRoutes,
    ...expeditionHqRoutes,
    ...fundraisingRoutes,
    ...livingMemoryRoutes,
  ],
})

export default router
