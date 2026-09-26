import { defineModule } from '@/core/module'

/**
 * «Звание по метке»: судье подносят NFC-метку — и он сразу поисковик или
 * краевед, без заявки и администратора. Костыль для показа приложения.
 *
 * Меток две, на каждой ссылка `marshruty://grant?k=<ключ>`; какую роль даёт
 * ключ, знает только сервис (`POST /role-grants/redeem` в user_service).
 * Экран открывает сама метка (`features/role-grant`, с любого экрана и из
 * закрытого приложения) или та же ссылка из QR-кода.
 *
 * Без входа экран не открыть: роль выдаётся аккаунту, который открыт на
 * телефоне, — охрана роутера отправит на вход и вернёт сюда.
 *
 * В браузере с `VITE_MOCK_NEW_API=true`: `/grant?k=demo-searcher` и
 * `/grant?k=demo-historian` — посмотреть праздник без меток и сервера.
 */
export default defineModule({
  id: 'role-grant',
  routes: [
    {
      path: '/grant',
      name: 'role-grant',
      component: () => import('./RoleGrantPage.vue'),
      meta: { title: 'Звание', layout: 'bare' },
    },
  ],
})
