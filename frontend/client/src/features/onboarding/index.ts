/**
 * Обучение: приветствие поверх любого экрана и память о том, что его видели.
 *
 * Корень приложения ставит `WelcomeSheet` один раз. Сами разделы и слайды
 * живут в модуле `modules/onboarding` — здесь только то, что нужно и корню,
 * и модулю: когда здороваться и что человек уже закрыл.
 */
export { default as WelcomeSheet } from './WelcomeSheet.vue'
export { default as HelpButton } from './HelpButton.vue'
export { TOUR_VERSION, forgetOnboarding, markSeen, needsWelcome, seenVersion } from './state'
