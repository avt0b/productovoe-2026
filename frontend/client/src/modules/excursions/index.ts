import { defineModule } from '@/core/module'

/**
 * Экскурсии краеведов: запись заранее и сбор группы бампом на месте.
 *
 * Данные — `search_hq_service` (`/excursions`). Запись, открытие сбора и
 * встряска идут от имени человека, поэтому нужен вход по почте: в демо-режиме
 * без аккаунта экраны показывают, что нужно войти.
 */
export default defineModule({
  id: 'excursions',
  tab: { title: 'Экскурсии', icon: 'groups', route: 'excursions', order: 15 },
  routes: [
    {
      path: '/excursions',
      name: 'excursions',
      component: () => import('./ExcursionsPage.vue'),
      meta: { title: 'Экскурсии' },
    },
    {
      path: '/excursions/new',
      name: 'excursion-new',
      component: () => import('./NewExcursionPage.vue'),
      meta: { title: 'Новая экскурсия', layout: 'detail', tab: 'excursions' },
    },
    {
      path: '/excursions/:excursionId/edit',
      name: 'excursion-edit',
      component: () => import('./NewExcursionPage.vue'),
      meta: { title: 'Изменить экскурсию', layout: 'detail', tab: 'excursions' },
    },
    {
      path: '/excursions/:excursionId',
      name: 'excursion',
      component: () => import('./ExcursionPage.vue'),
      props: true,
      meta: { title: 'Экскурсия', layout: 'detail', tab: 'excursions' },
    },
    {
      path: '/excursions/:excursionId/gathering',
      name: 'excursion-gathering',
      component: () => import('./GatheringPage.vue'),
      props: true,
      meta: { title: 'Сбор группы', layout: 'detail', tab: 'excursions' },
    },
    {
      // Полноэкранная карта: группа идёт, шапка и вкладки только мешали бы.
      path: '/excursions/:excursionId/walk',
      name: 'excursion-walk',
      component: () => import('./WalkPage.vue'),
      props: true,
      meta: { title: 'Группа идёт', layout: 'bare', tab: 'excursions' },
    },
  ],
})
