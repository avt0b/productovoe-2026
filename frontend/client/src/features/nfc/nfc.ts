import { Capacitor, registerPlugin, type PluginListenerHandle } from '@capacitor/core'
import type { Router } from 'vue-router'

import { appLinkPath } from '@/core/deeplinks'

/**
 * NFC-метки: что лежит на метке и как записать свою.
 *
 * Читает нативный плагин `MarshrutyNfc` (`android/app/src/main/java/.../nfc`).
 * Пока экран открыт, метки ловит режим чтения; метка с нашей ссылкой
 * (`marshruty://nfc…`) открывает приложение и закрытым — тогда она приходит
 * через `consumeLaunchTag`.
 *
 * В браузере NFC нет: `isNfcAvailable()` вернёт `false`, экран это объяснит.
 */

export interface NfcRecord {
  kind: 'text' | 'uri' | 'mime' | 'unknown'
  text?: string
  uri?: string
  mime?: string
}

export interface NfcTag {
  /** Серийный номер метки, как его отдаёт телефон. */
  id: string | null
  /** Технологии метки: NfcA, Ndef, MifareUltralight… */
  techs: string[]
  /** Можно ли на неё писать. */
  writable: boolean
  /** Сколько байт помещается, если метка это сообщает. */
  maxSize: number | null
  records: NfcRecord[]
  /** Метку унесли раньше, чем успели прочитать. */
  error?: string
}

export interface NfcStatus {
  supported: boolean
  enabled: boolean
}

export interface NfcWritePayload {
  text?: string
  uri?: string
}

interface NfcPluginApi {
  status(): Promise<NfcStatus>
  startScan(): Promise<void>
  stopScan(): Promise<void>
  write(payload: NfcWritePayload): Promise<{ tag: NfcTag }>
  cancelWrite(): Promise<void>
  consumeLaunchTag(): Promise<{ tag?: NfcTag }>
  openSettings(): Promise<void>
  addListener(event: 'nfcTag', handler: (tag: NfcTag) => void): Promise<PluginListenerHandle>
  addListener(event: 'nfcLink', handler: (link: { url: string }) => void): Promise<PluginListenerHandle>
}

const plugin = registerPlugin<NfcPluginApi>('MarshrutyNfc')

/** NFC есть только в приложении на телефоне. */
export function isNfcAvailable(): boolean {
  return Capacitor.isNativePlatform() && Capacitor.isPluginAvailable('MarshrutyNfc')
}

export function nfcStatus(): Promise<NfcStatus> {
  return plugin.status()
}

export function startNfcScan(): Promise<void> {
  return plugin.startScan()
}

export function stopNfcScan(): Promise<void> {
  return plugin.stopScan()
}

export function onNfcTag(handler: (tag: NfcTag) => void): Promise<PluginListenerHandle> {
  return plugin.addListener('nfcTag', handler)
}

/** Записать на следующую приложенную метку. Ответ придёт, когда её приложат. */
export function writeNfcTag(payload: NfcWritePayload): Promise<{ tag: NfcTag }> {
  return plugin.write(payload)
}

export function cancelNfcWrite(): Promise<void> {
  return plugin.cancelWrite()
}

/** Метка, которой открыли приложение. Отдаётся один раз. */
export async function consumeLaunchTag(): Promise<NfcTag | null> {
  if (!isNfcAvailable()) return null
  const { tag } = await plugin.consumeLaunchTag()
  return tag ?? null
}

export function openNfcSettings(): Promise<void> {
  return plugin.openSettings()
}

/** Первая осмысленная запись метки: ссылка или текст. */
export function tagPayload(tag: NfcTag): NfcRecord | null {
  return tag.records.find((record) => record.uri || record.text) ?? null
}

/** Ссылка внутри приложения: `marshruty://routes/abc` → `/routes/abc`. */
export function appPath(uri: string | undefined): string | null {
  return appLinkPath(uri)
}

/**
 * Метка с нашей ссылкой открывает свой экран — где бы человек ни был и даже
 * если приложение было закрыто: ссылку с системного запуска меткой присылает
 * плагин (`nfcLink`). Метки, прочитанные на экране NFC, сюда не попадают — там
 * человек сам решает, открывать ли ссылку.
 */
export function listenNfcLinks(router: Router): void {
  if (!isNfcAvailable()) return
  void plugin.addListener('nfcLink', ({ url }) => {
    // На экране NFC метки пишут и прикладывают для проверки — не уводим с него.
    if (router.currentRoute.value.name === 'nfc') return
    const path = appLinkPath(url)
    if (!path) return
    const target = router.resolve(path)
    // Экран, на который ведёт метка, мог уйти из сборки вместе со своим модулем.
    if (!target.matched.length) return
    // Сама метка ждёт экран NFC; раз ведёт не туда, показывать её потом незачем.
    if (target.name !== 'nfc') void consumeLaunchTag()
    void router.push(path)
  })
}
