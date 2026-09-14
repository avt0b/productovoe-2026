import { defineModule } from '@/core/module'

/**
 * Точка маршрута: сравнение «тогда и сейчас», голоса эпохи, семейный квест.
 *
 * Своей вкладки у окна нет — сюда приходят с карты маршрутов. Путь вложен в
 * `/routes`, но модуль самостоятельный: без карты точка открывается по ссылке.
 */
export default defineModule({
  id: 'route-point',
  routes: [
    {
      path: '/routes/:pointId',
      name: 'route-point',
      component: () => import('./RoutePointPage.vue'),
      props: true,
      meta: { title: 'Точка маршрута', layout: 'detail', tab: 'routes' },
    },
  ],
})
