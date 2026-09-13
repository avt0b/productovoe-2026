/// <reference types="vite/client" />

// Шима для *.vue здесь намеренно нет: vue-tsc разбирает SFC сам, а ручная
// декларация превратила бы все компоненты в `any` и убила проверку пропсов.

interface ImportMetaEnv {
  /** Адрес `map_service`: слой «ВОВ» и «Последний бой». По умолчанию — http://127.0.0.1:8003. */
  readonly VITE_MAP_API_URL?: string
  /** Адрес `route_service`: семейные маршруты. По умолчанию — http://127.0.0.1:8006. */
  readonly VITE_ROUTE_API_URL?: string
  /** Шаблон тайлов подложки в формате Leaflet (`{z}/{x}/{y}`). По умолчанию — CARTO Voyager. */
  readonly VITE_MAP_TILES_URL?: string
  /** Подпись правообладателей подложки. Меняете тайлы — меняйте и её. */
  readonly VITE_MAP_TILES_ATTRIBUTION?: string
}
