/**
 * NFC-метки: приложил телефон к табличке — увидел, что на ней.
 *
 * Мысль такая: у памятника или на точке маршрута висит метка, человек
 * подносит телефон и попадает сразу на нужный экран — без поиска по карте.
 * Пока это самостоятельная механика: окно `modules/nfc` показывает, что на
 * метке, и умеет записывать свои метки. Прикрутить к другим окнам — позвать
 * `useNfcScanner` там, где нужно, или открыть экран `{ name: 'nfc' }`.
 *
 * Метка с нашей ссылкой (`marshruty://…`) открывает свой экран сама, где бы
 * человек ни был и даже при закрытом приложении, — это `listenNfcLinks`,
 * он подключён в `main.ts`.
 *
 * Сам разбор меток — нативный плагин `MarshrutyNfc` в APK. В браузере NFC нет.
 */
export { default as NfcTagSheet } from './NfcTagSheet.vue'
export {
  appPath,
  cancelNfcWrite,
  consumeLaunchTag,
  isNfcAvailable,
  listenNfcLinks,
  nfcStatus,
  openNfcSettings,
  tagPayload,
  writeNfcTag,
  type NfcRecord,
  type NfcStatus,
  type NfcTag,
  type NfcWritePayload,
} from './nfc'
export { useNfcScanner } from './useNfcScanner'
