import { Browser } from '@capacitor/browser'
import { Capacitor } from '@capacitor/core'

import { apiRequest } from '@/core/api'

import { fromExternalLogin, type ExternalCompleteDto } from './serviceAuthProvider'
import type { SignInResult } from './types'

/**
 * Вход через VK ID, MAX и Госуслуги — ручки `auth_service` `/auth/external/*`.
 *
 * 1. `start` — сервис отдаёт `login_id` (секрет попытки, хранится здесь) и
 *    адрес подтверждения у провайдера.
 * 2. Человек подтверждает вход у провайдера. VK ID и Госуслуги возвращают его
 *    в приложение с одноразовым `result_code`: в APK — ссылкой
 *    `marshruty://auth/external`, в браузере — на `/auth/external`. MAX
 *    подтверждает вход через бота, возврата нет — приложение само спрашивает,
 *    готово ли.
 * 3. `complete` — пара токенов, как у входа по паролю. Пока вход не
 *    подтверждён, сервис отвечает «ещё ждём».
 *
 * Токены в адрес не попадают никогда: без `login_id` с этого устройства код из
 * ссылки бесполезен.
 */

export type ExternalProvider = 'vk' | 'max' | 'gosuslugi'

export interface ProviderInfo {
  provider: ExternalProvider
  title: string
  /** Кнопку можно нажать: провайдер настроен или включён тестовый режим. */
  enabled: boolean
  kind: 'redirect' | 'bot'
  /** Тестовая страница вместо настоящего провайдера. */
  mock: boolean
}

interface StartDto {
  login_id: string
  provider: ExternalProvider
  authorize_url: string
  kind: 'redirect' | 'bot'
  expires_in: number
}

export interface PendingLogin {
  loginId: string
  provider: ExternalProvider
  kind: 'redirect' | 'bot'
  /** Когда попытка истекает, мс unix-времени. */
  expiresAt: number
}

const PENDING_KEY = 'marshruty.client.external-login'

/** Адрес возврата после подтверждения у провайдера. Сервис пускает только разрешённые. */
export function externalReturnUrl(): string {
  return Capacitor.isNativePlatform() ? 'marshruty://auth/external' : `${window.location.origin}/auth/external`
}

export function listProviders(): Promise<ProviderInfo[]> {
  return apiRequest('GET', 'auth', '/auth/external/providers')
}

export function readPendingLogin(): PendingLogin | null {
  try {
    const pending = JSON.parse(localStorage.getItem(PENDING_KEY) ?? 'null') as PendingLogin | null
    return pending && pending.expiresAt > Date.now() ? pending : null
  } catch {
    return null
  }
}

export function clearPendingLogin(): void {
  try {
    localStorage.removeItem(PENDING_KEY)
  } catch {
    /* приватный режим — попытка и так не сохранилась */
  }
}

/**
 * Начать вход и открыть подтверждение у провайдера. В браузере страница уходит
 * к провайдеру и вернётся на `/auth/external`; в APK открывается системный
 * браузер, а приложение ждёт ссылку `marshruty://`.
 */
export async function startExternalLogin(provider: ExternalProvider): Promise<PendingLogin> {
  const started = await apiRequest<StartDto>('POST', 'auth', `/auth/external/${provider}/start`, {
    body: { return_to: externalReturnUrl() },
  })
  const pending: PendingLogin = {
    loginId: started.login_id,
    provider: started.provider,
    kind: started.kind,
    expiresAt: Date.now() + started.expires_in * 1000,
  }
  try {
    localStorage.setItem(PENDING_KEY, JSON.stringify(pending))
  } catch {
    /* приватный режим — в браузере после возврата попытку не найти, в APK хватит памяти */
  }

  if (Capacitor.isNativePlatform()) await Browser.open({ url: started.authorize_url })
  else if (started.kind === 'redirect') window.location.assign(started.authorize_url)
  // Бот MAX — в новой вкладке: эта остаётся ждать подтверждения.
  else window.open(started.authorize_url, '_blank', 'noopener')
  return pending
}

/**
 * Забрать токены. `null` — вход ещё не подтверждён, спросить ещё раз позже.
 * `resultCode` — из ссылки возврата; у входа через бота его нет.
 */
export async function completeExternalLogin(pending: PendingLogin, resultCode: string | null): Promise<SignInResult | null> {
  const response = await apiRequest<ExternalCompleteDto | { status: 'pending' }>('POST', 'auth', '/auth/external/complete', {
    body: { login_id: pending.loginId, result_code: resultCode },
  })
  if ('status' in response && response.status === 'pending') return null
  clearPendingLogin()
  return fromExternalLogin(response as ExternalCompleteDto)
}

/** Закрыть системный браузер после возврата в приложение. На Android вкладка закрывается сама. */
export function closeExternalBrowser(): void {
  if (Capacitor.isNativePlatform()) void Browser.close().catch(() => undefined)
}
