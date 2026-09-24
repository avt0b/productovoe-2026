/**
 * Чат сбора и выезда: переписка группы, которую окна встраивают одним окном.
 * Кому можно писать, решает `search_hq_service` — участнику экскурсии или
 * волонтёру выезда; остальным ручка ответит 403.
 */
export { default as ChatSheet } from './ChatSheet.vue'
export type { ChatMessage, ChatSubject } from './api'
