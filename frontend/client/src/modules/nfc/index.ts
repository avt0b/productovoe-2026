import { defineModule } from '@/core/module'

/**
 * «NFC-метка»: приложить телефон к метке и увидеть, что на ней.
 *
 * Пока модуль сам по себе — вкладки в нижней панели у него нет. Открыть:
 *
 * - метка со ссылкой `marshruty://nfc` открывает экран сама, даже если
 *   приложение закрыто (intent-filter в `AndroidManifest.xml`);
 * - в разработке — адрес `/nfc`;
 * - из любого окна — `router.push({ name: 'nfc' })` с проверкой
 *   `router.hasRoute('nfc')`.
 *
 * Прикрутить метки к точкам маршрута и памятникам — записать на метку ссылку
 * вида `marshruty://routes/<точка>?route=<маршрут>` (экран это умеет) и звать
 * `useNfcScanner` из нужного окна.
 */
export default defineModule({
  id: 'nfc',
  routes: [
    {
      path: '/nfc',
      name: 'nfc',
      component: () => import('./NfcPage.vue'),
      meta: { title: 'NFC-метка', layout: 'detail', public: true },
    },
  ],
})
