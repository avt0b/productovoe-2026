import { defineModule } from '@/core/module'

/** «Память»: оживший портрет героя из семейного архива. */
export default defineModule({
  id: 'memory',
  tab: { title: 'Память', icon: 'auto_awesome', route: 'memory', order: 40 },
  routes: [
    {
      path: '/memory',
      name: 'memory',
      component: () => import('./MemoryPage.vue'),
      meta: { title: 'Память' },
    },
  ],
})
