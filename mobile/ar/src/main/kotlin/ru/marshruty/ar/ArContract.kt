package ru.marshruty.ar

import ru.marshruty.ar.domain.GeoPoint

/**
 * Публичный контракт AR-модуля.
 *
 * Модуль ничего не знает о хосте: ни о навигации приложения, ни о его сети,
 * ни о том, Compose там или WebView. Хост собирает [ArPointSpec], запускает
 * экран и получает [ArResult]. Всё.
 */

/** Что должен сказать проводник на точке. */
data class NarrationSpec(
    /** Локальный файл или URL заранее синтезированной озвучки. */
    val audioUri: String?,
    /** Субтитры обязательны: на улице шумно, и часть детей читает, а не слушает. */
    val subtitles: List<SubtitleLine>,
)

/** Строка субтитров с таймкодом от начала аудио. */
data class SubtitleLine(
    val fromMillis: Long,
    val toMillis: Long,
    val text: String,
)

/**
 * Персонаж-проводник.
 *
 * `null` в [ArPointSpec.companion] означает, что на этой точке проводника быть
 * не должно. Это не косметика: мультяшный маскот у братской могилы читается
 * как неуважение, поэтому решение принимает бэкенд (флаг у типа точки),
 * а модуль его исполняет.
 */
data class CompanionSpec(
    val name: String,
    val subtitle: String,
    /** Ассет персонажа: спрайт-лист или видео с альфа-каналом. */
    val assetUri: String,
)

/** Цель наведения на местности. */
data class ArTarget(
    val point: GeoPoint,
    /** Подпись у метки: «След кабельного окопа». */
    val label: String,
    /** Превышение над наблюдателем, метры. */
    val heightOffsetMeters: Double = 0.0,
)

/** Всё, что нужно AR-экрану для одной точки маршрута. */
data class ArPointSpec(
    val pointId: String,
    val title: String,
    val stepIndex: Int,
    val stepTotal: Int,
    val target: ArTarget?,
    val companion: CompanionSpec?,
    val narration: NarrationSpec,
) {
    init {
        require(stepTotal > 0) { "stepTotal должен быть положительным" }
        require(stepIndex in 1..stepTotal) { "stepIndex вне диапазона 1..$stepTotal" }
    }

    /** Прогресс сюжета для полосы вверху экрана. */
    val progress: Float get() = stepIndex.toFloat() / stepTotal
}

/** Чем закончился AR-эпизод. */
sealed interface ArResult {
    /** Цель найдена, рассказ дослушан — хост может засчитать точку. */
    data class Completed(val pointId: String) : ArResult

    /** Пользователь вышел сам. */
    data class Dismissed(val pointId: String) : ArResult

    /**
     * Экран не смог работать: нет разрешения на камеру, нет самой камеры,
     * нет датчика ориентации. Хост показывает обычную карточку точки.
     */
    data class Unavailable(val pointId: String, val reason: Reason) : ArResult {
        enum class Reason { CAMERA_PERMISSION_DENIED, NO_CAMERA, NO_ORIENTATION_SENSOR }
    }
}
