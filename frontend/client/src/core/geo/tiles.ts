/**
 * Подложка карты.
 *
 * По умолчанию — растровые тайлы CARTO Voyager на данных OpenStreetMap.
 * Не `tile.openstreetmap.org`: это общественный ресурс со строгими правилами,
 * он не рассчитан на нагрузку из приложений. У CARTO есть бесплатный лимит для
 * некоммерческих проектов — на хакатон и пилот хватит; для прода нужен свой
 * тайл-сервер или договор с 2ГИС. Подложка меняется в `.env.local`, код не
 * трогаем.
 */
export const TILES = {
  url: import.meta.env.VITE_MAP_TILES_URL || 'https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png',
  attribution:
    import.meta.env.VITE_MAP_TILES_ATTRIBUTION ||
    '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>',
  subdomains: 'abcd',
  maxZoom: 19,
} as const
