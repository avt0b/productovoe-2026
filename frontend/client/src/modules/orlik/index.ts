import { defineModule } from '@/core/module'

import { isOrlikCode } from './letter'

/**
 * «Орлик»: благодарственное письмо от команды battalion_404 на весь экран.
 *
 * Открывает его NFC-чип в фигурке орлика, которую вручают самым активным
 * участникам: на чипе ссылка `marshruty://orlik/b404-1943`. Всё зашито в
 * приложение — ни бэкенда, ни входа, ни интернета не нужно.
 *
 * Своей вкладки нет — экран открывают только фигуркой.
 */
export default defineModule({
  id: 'orlik',
  routes: [
    {
      path: '/orlik/:code',
      name: 'orlik',
      component: () => import('./OrlikPage.vue'),
      meta: { title: 'Благодарственное письмо', layout: 'bare', public: true },
      // Чужой код — не наша фигурка: письма нет, ведём на главную.
      beforeEnter: (to) => isOrlikCode(String(to.params.code)) || { name: 'home' },
    },
  ],
})
