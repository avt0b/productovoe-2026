import { defineModule } from '@/core/module'

/** «Последний бой»: гео-реестр мест боёв и находок, помощь поисковикам. */
export default defineModule({
  id: 'last-stand',
  tab: { title: 'Последний бой', icon: 'verified', route: 'last-stand', order: 20 },
  routes: [
    {
      path: '/last-stand',
      name: 'last-stand',
      component: () => import('./LastStandPage.vue'),
      meta: { title: 'Последний бой' },
    },
  ],
})
