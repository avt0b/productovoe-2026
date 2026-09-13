import { defineModule } from '@/core/module'

/** «Штаб»: итоги экспедиционного сезона, сборы отрядов, выезды с поисковиками. */
export default defineModule({
  id: 'hq',
  tab: { title: 'Штаб', icon: 'volunteer_activism', route: 'hq', order: 30 },
  routes: [
    {
      path: '/hq',
      name: 'hq',
      component: () => import('./HqPage.vue'),
      meta: { title: 'Штаб' },
    },
  ],
})
