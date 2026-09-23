package ru.marshruty.ar.domain

/**
 * Где лежит озвучка точки.
 *
 * Строку `NarrationSpec.audioUri` собирает хост, и ошибиться в ней легче, чем
 * в остальном контракте: один прислал `asset:///narration/wp-2.ogg`, другой —
 * просто `narration/wp-2.ogg`, третий — ссылку из media_service. Поэтому
 * разбор живёт здесь, чистой функцией, и проверяется на JVM, а не на телефоне
 * посреди экскурсии.
 */
sealed interface NarrationAudio {
    /** Файл внутри `assets`: открывается через `AssetManager`, а не по пути. */
    data class Asset(val path: String) : NarrationAudio

    /** Всё, что Android открывает сам: `https://…`, `file://…`, `content://…`, `/sdcard/…`. */
    data class Uri(val value: String) : NarrationAudio
}

/** `scheme://` в начале строки. */
private val SCHEME = Regex("^[a-zA-Z][a-zA-Z0-9+.\\-]*://")

private const val ASSET_SCHEME = "asset://"

/**
 * Разбор `NarrationSpec.audioUri`.
 *
 * `null` — озвучки нет. Это штатный случай, а не ошибка: на точку могли не
 * записать голос, и тогда рассказ идёт одними субтитрами.
 */
fun narrationAudioOf(audioUri: String?): NarrationAudio? {
    val raw = audioUri?.trim().orEmpty()
    if (raw.isEmpty()) return null

    if (raw.startsWith(ASSET_SCHEME, ignoreCase = true)) {
        // `asset:///narration/wp-2.ogg` и `asset://narration/wp-2.ogg` — одно и то же:
        // пустой хост в первом виде даёт лишний слэш, AssetManager его не примет.
        val path = raw.substring(ASSET_SCHEME.length).trimStart('/')
        return if (path.isEmpty()) null else NarrationAudio.Asset(path)
    }
    // Абсолютный путь — тоже файл, а не ассет: `/sdcard/Download/wp-2.ogg`.
    if (SCHEME.containsMatchIn(raw) || raw.startsWith("/")) return NarrationAudio.Uri(raw)

    return NarrationAudio.Asset(raw)
}

/**
 * Позиция рассказа, мс.
 *
 * Пока звучит озвучка, время задаёт плеер: свои часы с ним разойдутся —
 * плеер догоняет буфер, отстаёт на паузе в звонке, а часы экрана идут ровно, и
 * субтитры уезжают от голоса. Без озвучки остаются часы: текст на улице чаще
 * читают, чем слушают, и он должен идти в любом случае.
 */
fun narrationPositionMillis(
    audioPositionMillis: Long?,
    clockMillis: Long,
    startedAtMillis: Long,
): Long = audioPositionMillis ?: (clockMillis - startedAtMillis).coerceAtLeast(0L)
