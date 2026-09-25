import { defineModule } from '@/core/module'

/**
 * Обучение: «что где в приложении».
 *
 * Вкладки в нижней панели у модуля нет — их пять и панель заполнена. Открыть:
 *
 * - при первом входе приветствие (`features/onboarding`) само предложит
 *   пройти обучение: `/onboarding?tour=1`;
 * - из профиля и с экранов — `router.push({ name: 'onboarding' })`
 *   с проверкой `router.hasRoute('onboarding')`;
 * - в разработке — адрес `/onboarding`.
 *
 * Появился новый раздел приложения — допишите его в `data.ts` и поднимите
 * `TOUR_VERSION` в `features/onboarding/state.ts`: тогда приветствие покажем
 * ещё раз тем, кто его уже закрыл.
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
