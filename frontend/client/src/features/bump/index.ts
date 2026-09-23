/**
 * Бамп: двое встряхивают телефоны в одном месте и в одно время — сервер
 * засчитывает встречу. На экскурсии так краевед отмечает, что участник пришёл.
 *
 * Снаружи — только то, что здесь экспортировано. Пороги датчика, тексты,
 * анимация «Вы вместе!» правятся внутри папки, экран экскурсии не трогается.
 */
export { default as BumpPad } from './BumpPad.vue'
export { default as TogetherOverlay } from './TogetherOverlay.vue'
export type { BumpOutcome, BumpResult } from './api'
export { useBump, type BumpCelebration, type BumpNotice, type BumpOptions } from './useBump'
export type { ShakeOptions, ShakeStatus } from './useShake'
