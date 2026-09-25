/**
 * Карточка точки и маршрут до неё: нажали метку — внизу раскрытой карты
 * карточка места, «Начать маршрут» сам определяет, где человек, и прокладывает
 * путь (рядом — пешком, дальше — на машине), перестраивая его по ходу.
 *
 * Окно заводит один `usePointRoute` на карту, рисует его `path`, отдаёт карте
 * `focus` и кладёт `PointSheet` в слот `sheet` у `GeoMap`. Тексты, пороги
 * перестройки и вид карточки правятся здесь, окна не трогаются.
 */
export { default as PointSheet } from './PointSheet.vue'
export {
  usePointRoute,
  type GeoSource,
  type PointRoute,
  type PointRouteState,
  type RouteTarget,
} from './usePointRoute'
