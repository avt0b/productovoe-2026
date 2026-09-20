/**
 * AR-поиск на точке маршрута.
 *
 * Сам экран — нативный модуль `mobile/ar` (камера, компас, ARCore): в APK он
 * подключается готовым AAR, а отсюда только запускается. В браузере AR нет —
 * `isArAvailable()` вернёт `false`, и окно покажет подсказку вместо кнопки.
 *
 * Править AR — это `mobile/ar` (что рисуем и как наводим) и эта папка (что за
 * точку туда отдаём). Окно «Точка маршрута» знает только `openAr` и результат.
 */
export { default as ArHintCard } from './ArHintCard.vue'
export {
  buildSubtitles,
  isArAvailable,
  openAr,
  type ArOutcome,
  type ArPoint,
  type ArResult,
  type ArSubtitle,
} from './ar'
