import { defineModule } from '@/core/module'

/**
 * «Память»: «Живое фото» (media_service), народный архив и его проверка
 * краеведом (archive_service). Вкладка — в адресе: `?tab=archive`,
 * `?propose=soldier_card` сразу открывает форму карточки бойца.
 */
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
