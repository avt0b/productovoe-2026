/**
 * Куда приложение ходит за данными.
 *
 * Адреса задаются на сборке — по одному на сервис (`.env.local`,
 * `.env.android.local`, образец — `.env.example`). Шлюз пишется так же, полным
 * адресом с префиксом: `VITE_USER_API_URL=https://marshruty.ru/api/users`. Для
 * APK на телефоне нужен адрес компьютера в локальной сети: `127.0.0.1` на
 * телефоне — это сам телефон.
 */

export type ServiceName = 'auth' | 'users' | 'map' | 'hq' | 'archive' | 'routes' | 'media'

function trimSlash(value: string): string {
  return value.replace(/\/+$/, '')
}

/** Адреса из сборки. Без `.env.local` — сервисы на этом же компьютере (порты — `backend/README.md`). */
const BUILD_URLS: Record<ServiceName, string> = {
  auth: trimSlash(import.meta.env.VITE_AUTH_API_URL || 'http://127.0.0.1:8001'),
  users: trimSlash(import.meta.env.VITE_USER_API_URL || 'http://127.0.0.1:8002'),
  map: trimSlash(import.meta.env.VITE_MAP_API_URL || 'http://127.0.0.1:8003'),
  hq: trimSlash(import.meta.env.VITE_HQ_API_URL || 'http://127.0.0.1:8004'),
  archive: trimSlash(import.meta.env.VITE_ARCHIVE_API_URL || 'http://127.0.0.1:8005'),
  routes: trimSlash(import.meta.env.VITE_ROUTE_API_URL || 'http://127.0.0.1:8006'),
  media: trimSlash(import.meta.env.VITE_MEDIA_API_URL || 'http://127.0.0.1:8007'),
}

/** Адрес сервиса, по которому идут запросы. */
export function serviceBaseUrl(service: ServiceName): string {
  return BUILD_URLS[service]
}
