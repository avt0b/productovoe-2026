import { defineModule } from '@/core/module'

/**
 * Обучение: «что где в приложении».
 *
 * Вкладки в нижней панели у модуля нет — их шесть и панель заполнена. Открыть:
 *
 * - при первом входе приветствие (`features/onboarding`) само предложит
 *   пройти обучение: `/onboarding?tour=1`;
 * - одной главой — `/onboarding?tour=<глава>` (`id` главы из `data.ts`):
 *   так из шпаргалки возвращаются за одним разделом;
 * - из профиля и с экранов — `router.push({ name: 'onboarding' })`
 *   с проверкой `router.hasRoute('onboarding')`;
 * - в разработке — адрес `/onboarding`.
 *
 * Появилась новая возможность — допишите шаг в свою главу в `data.ts`, новый
 * раздел — целую главу, и поднимите `TOUR_VERSION` в
 * `features/onboarding/state.ts`: тогда приветствие покажем ещё раз тем, кто
 * его уже закрыл.
 */
export default defineModule({
  id: 'onboarding',
  routes: [
    {
      path: '/onboarding',
      name: 'onboarding',
      component: () => import('./OnboardingPage.vue'),
      meta: { title: 'Как всё устроено', layout: 'detail', public: true },
    },
  ],
})
