import { defineModule } from '@/core/module'

/** Карта маршрутов: поиск, фильтры, нарисованная карта с метками и маршрут дня. */
export default defineModule({
  id: 'routes',
  tab: { title: 'Маршруты', icon: 'explore', route: 'routes', order: 10 },
  routes: [
    {
      path: '/routes',
      name: 'routes',
      component: () => import('./RoutesPage.vue'),
      meta: { title: 'Маршруты' },
    },
  ],
})
