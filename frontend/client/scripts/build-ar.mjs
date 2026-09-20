/**
 * Собирает AR-модуль из `mobile/` и кладёт AAR в локальный репозиторий
 * `mobile/ar/build/repo`, откуда его берёт сборка APK.
 *
 * Отдельная сборка нужна потому, что AR собран на AGP 9, а шаблон Capacitor —
 * на AGP 8: две версии AGP в одной сборке Gradle не уживаются.
 *
 * Прокси Gradle сам не подхватывает — если в окружении есть HTTPS_PROXY,
 * передаём его явно.
 */
import { spawnSync } from 'node:child_process'
import { existsSync } from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const mobileDir = path.resolve(fileURLToPath(new URL('../../../mobile', import.meta.url)))
const wrapper = process.platform === 'win32' ? 'gradlew.bat' : './gradlew'

if (!existsSync(path.join(mobileDir, wrapper))) {
  console.error(`AR-модуль не найден: ${mobileDir}. Он лежит в этом же репозитории, в папке mobile/.`)
  process.exit(1)
}

const proxy = process.env.HTTPS_PROXY ?? process.env.https_proxy
const proxyArgs = []
if (proxy) {
  const { hostname, port } = new URL(proxy)
  for (const scheme of ['https', 'http']) {
    proxyArgs.push(`-D${scheme}.proxyHost=${hostname}`, `-D${scheme}.proxyPort=${port || '80'}`)
  }
}

const result = spawnSync(wrapper, [':ar:publishReleasePublicationToLocalRepository', '--console=plain', ...proxyArgs], {
  cwd: mobileDir,
  stdio: 'inherit',
  shell: process.platform === 'win32',
})

process.exit(result.status ?? 1)
