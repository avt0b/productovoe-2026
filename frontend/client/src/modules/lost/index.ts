import { defineModule } from '@/core/module'

export default defineModule({
  id: 'lost',
  routes: [
    {
      // Полноэкранная карта, как прогулка: шапка и вкладки только мешали бы искать.
      path: '/lost/:alertId',
      name: 'lost-alert',
      component: () => import('./LostAlertPage.vue'),
      props: true,
      meta: { title: 'Поиск', layout: 'bare', tab: 'excursions' },
    },
  ],
})
