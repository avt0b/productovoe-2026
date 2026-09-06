package ru.marshruty.ar.sim

import ru.marshruty.ar.ArPointSpec
import ru.marshruty.ar.ArTarget
import ru.marshruty.ar.CompanionSpec
import ru.marshruty.ar.NarrationSpec
import ru.marshruty.ar.SubtitleLine
import ru.marshruty.ar.domain.DeviceOrientation
import ru.marshruty.ar.domain.GeoPoint
import ru.marshruty.ar.domain.LocationFix
import ru.marshruty.ar.domain.bearingDegrees

/**
 * Сценарий для превью, тестов и показа.
 *
 * В зале защиты нет ни неба, ни ориентиров, ни нормального GPS — тыкать
 * телефоном в стену и надеяться, что метка встанет куда надо, нельзя. Поэтому
 * источники ориентации и гео подменяются записанным треком, а кадр камеры —
 * статичной картинкой.
 */
object Simulation {

    /** Наблюдатель: опушка у Вязовицы, Орловская область. */
    val Observer = GeoPoint(latitude = 52.9700, longitude = 36.0665)

    /** Цель: след кабельного окопа, примерно в 18 метрах северо-восточнее. */
    val Target = GeoPoint(latitude = 52.97012, longitude = 36.06673)

    val companion = CompanionSpec(
        name = "Санитарный пёс Верный",
        subtitle = "41-й СП",
        assetUri = "asset:///companion/verny.webp",
    )

    val point = ArPointSpec(
        pointId = "wp-2",
        title = "Рубеж связистов",
        stepIndex = 2,
        stepTotal = 4,
        target = ArTarget(point = Target, label = "След кабельного окопа"),
        companion = companion,
        narration = NarrationSpec(
            audioUri = "asset:///narration/wp-2.ogg",
            subtitles = listOf(
                SubtitleLine(
                    0, 6_000,
                    "Здесь, у этой опушки, в октябре сорок первого держали рубеж " +
                        "связисты 41-го стрелкового полка…",
                ),
                SubtitleLine(
                    6_000, 12_000,
                    "Они тянули провод под огнём, чтобы штаб не потерял связь с батареей.",
                ),
                SubtitleLine(
                    12_000, 18_000,
                    "Давай найдём след окопа вон за той берёзой!",
                ),
            ),
        ),
    )

    /** Точка без проводника: у братской могилы маскот неуместен. */
    val memorialPoint = point.copy(
        pointId = "wp-4",
        title = "Братская могила",
        stepIndex = 4,
        companion = null,
        target = null,
    )

    val fix = LocationFix(point = Observer, accuracyMeters = 6.0)
    val poorFix = LocationFix(point = Observer, accuracyMeters = 95.0)

    /** Азимут, при котором цель окажется ровно по центру кадра. */
    val bearingToTarget: Double = bearingDegrees(Observer, Target)

    fun facingTarget(pitchDegrees: Double = -2.0) =
        DeviceOrientation(azimuthDegrees = bearingToTarget, pitchDegrees = pitchDegrees)

    fun turnedAwayBy(degrees: Double, pitchDegrees: Double = 0.0) =
        DeviceOrientation(azimuthDegrees = bearingToTarget + degrees, pitchDegrees = pitchDegrees)

    /**
     * Записанный «проход»: пользователь стоит боком, поворачивается к цели
     * и наводится на неё. Отдаётся кадрами по 100 мс.
     */
    fun scriptedTurn(steps: Int = 40): List<DeviceOrientation> {
        val startOffset = -70.0
        return (0 until steps).map { index ->
            val progress = index.toDouble() / (steps - 1).coerceAtLeast(1)
            // Замедление к концу: человек доводит камеру плавно, а не рывком.
            val eased = 1.0 - (1.0 - progress) * (1.0 - progress)
            turnedAwayBy(startOffset * (1.0 - eased), pitchDegrees = -2.0 * eased)
        }
    }
}
