import { defineModule } from '@/core/module'

export default defineModule({
  id: 'guides',
  routes: [
    {
      path: '/guides',
      name: 'guides',
      component: () => import('./GuidesRatingPage.vue'),
      meta: { title: 'Рейтинг краеведов', layout: 'detail', tab: 'excursions', public: true },
    },
    {
      path: '/guides/:guideId',
      name: 'guide',
      component: () => import('./GuidePage.vue'),
      props: true,
      meta: { title: 'Краевед', layout: 'detail', tab: 'excursions', public: true },
    },
  ],
})
