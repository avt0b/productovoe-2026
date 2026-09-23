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
) : java.io.Serializable

/** Строка субтитров с таймкодом от начала аудио. */
data class SubtitleLine(
    val fromMillis: Long,
    val toMillis: Long,
    val text: String,
) : java.io.Serializable {
    init {
        require(toMillis > fromMillis) { "Конец строки субтитров раньше начала" }
    }
}

/**
 * Строка, звучащая в данный момент, или null в паузе между репликами.
 * Границы: начало включительно, конец исключительно — соседние строки не
 * перекрываются на стыке.
 */
fun List<SubtitleLine>.lineAt(positionMillis: Long): SubtitleLine? =
    firstOrNull { positionMillis >= it.fromMillis && positionMillis < it.toMillis }

/**
 * Позиция, которая меняется только на границах строк.
 *
 * Экран перерисовывает субтитры, когда меняется позиция. Отдавать ему живые
 * миллисекунды — значит перерисовывать его каждый кадр, 120 раз в секунду на
 * таком телефоне, хотя строка сменится через шесть секунд. Здесь все моменты
 * одной строки сворачиваются в её начало, а пауза — в конец предыдущей:
 * [lineAt] от результата даёт ту же строку, что и от живой позиции.
 *
 * Строки должны идти по порядку и не перекрываться — как их и пишут.
 */
fun List<SubtitleLine>.stablePositionAt(positionMillis: Long): Long {
    val line = lastOrNull { it.fromMillis <= positionMillis } ?: return -1L
    return if (positionMillis < line.toMillis) line.fromMillis else line.toMillis
}

/**
 * Сколько длится рассказ, мс.
 *
 * Нужно там, где озвучки нет: иначе экран никогда не узнает, что рассказ
 * кончился, и проводник будет «говорить» молча до самого выхода.
 */
fun List<SubtitleLine>.durationMillis(): Long = maxOfOrNull { it.toMillis } ?: 0L

/** Состояние проигрывания рассказа. */
data class NarrationPlayback(
    val positionMillis: Long = 0L,
    val isPlaying: Boolean = false,
    val isMuted: Boolean = false,
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
    /**
     * Ассет персонажа внутри `assets`. Различается по расширению:
     *
     * - `companion/verny.glb` — 3D-модель glTF. Рисуется только в режиме
     *   маркера, где есть сцена ARCore; модель должна быть пропущена через
     *   tools/normalize_companion.py (рост 1.0, ноги на нуле, лицом к +Z);
     * - `companion/verny` — папка с кадрами `idle_000.png`,
     *   `talking_000.png`, `trick_000.png`. Достаточно одного
     *   `idle_000.png`: статичная картинка это клип из одного кадра.
     *
     * Покадровая ветка остаётся запасной: без маркера или без ARCore
     * экран показывает плоского персонажа, а не пустоту.
     */
    val assetUri: String,
) : java.io.Serializable

/** Цель наведения на местности. */
data class ArTarget(
    val point: GeoPoint,
    /** Подпись у метки: «След кабельного окопа». */
    val label: String,
    /** Превышение над наблюдателем, метры. */
    val heightOffsetMeters: Double = 0.0,
) : java.io.Serializable

/**
 * Картинка-маркер, на которую встаёт проводник.
 *
 * Компас и GPS дают направление с ошибкой в десятки метров и градусов — чтобы
 * показать «вон за той берёзой», этого хватает, а чтобы поставить персонажа
 * на конкретное место — нет: он будет плавать по кадру. Табличка на точке даёт
 * позу с точностью до сантиметров.
 *
 * Нужен ARCore. Если его на телефоне нет, экран работает как раньше — на компасе.
 */
data class MarkerSpec(
    /** Картинка внутри `assets`, например `markers/wp-2.png`. */
    val assetPath: String,
    /**
     * Ширина картинки, метры, или null — тогда ARCore измерит её сам.
     *
     * Известная ширина даёт точную позу с первого кадра — для напечатанной
     * таблички на точке её стоит указывать. Без ширины ARCore нужно пару секунд
     * движения камеры, зато картинку можно показать на экране любого размера.
     * Неверная ширина хуже отсутствующей: маркер на экране телефона шириной
     * 6 см при заявленных 30 см дал проводника впятеро больше таблички и мимо неё.
     */
    val physicalWidthMeters: Float? = null,
    /** Рост проводника, метры. null — чуть больше ширины таблички, заданной или измеренной. */
    val companionHeightMeters: Float? = null,
    /**
     * Через сколько миллисекунд без таблички поставить проводника перед камерой.
     * null — ждать табличку сколько угодно. Нужно там, где табличку сняли или
     * закрыли, и в зале защиты: пустой экран с «ищу» хуже персонажа рядом.
     * Найдётся табличка позже — проводник перейдёт на неё.
     */
    val fallbackInFrontAfterMillis: Long? = null,
) : java.io.Serializable {
    init {
        require(physicalWidthMeters == null || physicalWidthMeters > 0f) { "Ширина маркера должна быть положительной" }
        require(companionHeightMeters == null || companionHeightMeters > 0f) { "Рост проводника должен быть положительным" }
    }
}

/** Всё, что нужно AR-экрану для одной точки маршрута. */
data class ArPointSpec(
    val pointId: String,
    val title: String,
    val stepIndex: Int,
    val stepTotal: Int,
    val target: ArTarget?,
    val companion: CompanionSpec?,
    val narration: NarrationSpec,
    /** Табличка на точке. null — маркера нет, проводник показывается без привязки к месту. */
    val marker: MarkerSpec? = null,
) : java.io.Serializable {
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
