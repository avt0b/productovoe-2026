/**
 * Уведомления: плашка поверх любого экрана и опрос `user_service`.
 *
 * Корень приложения ставит `NotificationBanner` один раз — дальше фича сама
 * решает, что всплывать и куда вести. Новый вид уведомления — это новая
 * ветка в `useNotificationWatcher.toBanner`, экраны о нём не знают.
 */
export { default as NotificationBanner } from './NotificationBanner.vue'
export { fetchNotifications, markNotificationRead, type AppNotification } from './api'
