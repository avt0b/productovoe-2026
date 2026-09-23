/// <reference types="vite/client" />

// Шима для *.vue здесь намеренно нет: vue-tsc разбирает SFC сам, а ручная
// декларация превратила бы все компоненты в `any` и убила проверку пропсов.

interface ImportMetaEnv {
  /** Адрес `map_service`: слой «ВОВ» и «Последний бой». По умолчанию — http://127.0.0.1:8003. */
  readonly VITE_MAP_API_URL?: string
  /** Адрес `route_service`: семейные маршруты. По умолчанию — http://127.0.0.1:8006. */
  readonly VITE_ROUTE_API_URL?: string
  /** Адрес `auth_service`: вход и регистрация. По умолчанию — http://127.0.0.1:8001. */
  readonly VITE_AUTH_API_URL?: string
  /** Адрес `search_hq_service`: штаб, сборы, выезды, экскурсии и бамп. По умолчанию — http://127.0.0.1:8004. */
  readonly VITE_HQ_API_URL?: string
  /** Адрес `user_service`: профиль и достижения. По умолчанию — http://127.0.0.1:8002. */
  readonly VITE_USER_API_URL?: string
  /** Адрес `archive_service`: народный архив. По умолчанию — http://127.0.0.1:8005. */
  readonly VITE_ARCHIVE_API_URL?: string
  /** Адрес `media_service`: «Живое фото». По умолчанию — http://127.0.0.1:8007. */
  readonly VITE_MEDIA_API_URL?: string
  /** Шаблон тайлов подложки в формате Leaflet (`{z}/{x}/{y}`). По умолчанию — OpenStreetMap. */
  readonly VITE_MAP_TILES_URL?: string
  /** Подпись правообладателей подложки. Меняете тайлы — меняйте и её. */
  readonly VITE_MAP_TILES_ATTRIBUTION?: string
}
