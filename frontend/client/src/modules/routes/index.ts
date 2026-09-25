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
    // Пути редактора отдельные, а не `/routes/...`: там уже стоит карточка
    // точки (`/routes/:pointId` в модуле route-point).
    {
      path: '/my-routes',
      name: 'my-routes',
      component: () => import('./MyRoutesPage.vue'),
      meta: { title: 'Мои маршруты', layout: 'detail', tab: 'routes' },
    },
    {
      path: '/my-routes/:routeId',
      name: 'route-editor',
      component: () => import('./RouteEditorPage.vue'),
      meta: { title: 'Маршрут', layout: 'detail', tab: 'routes' },
    },
  ],
})
