/**
 * Подложка карты.
 *
 * По умолчанию — стандартные тайлы OpenStreetMap: без ключа, с русскими
 * подписями. Их правила разрешают умеренную нагрузку с подписью
 * правообладателей — на хакатон и демо хватит, но для прода нужен свой
 * тайл-сервер или договор с поставщиком (2ГИС, Яндекс).
 *
 * Бесплатные тайлы CARTO теперь без ключа рисуют поверх карты
 * «API KEY REQUIRED» — их по умолчанию не берём. Подложка меняется в
 * `.env.local`, код не трогаем.
 */
export const TILES = {
  url: import.meta.env.VITE_MAP_TILES_URL || 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
  attribution:
    import.meta.env.VITE_MAP_TILES_ATTRIBUTION ||
    '&copy; <a href="https://www.openstreetmap.org/copyright">участники OpenStreetMap</a>',
  maxZoom: 19,
} as const
