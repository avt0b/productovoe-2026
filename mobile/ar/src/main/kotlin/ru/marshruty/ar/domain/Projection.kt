package ru.marshruty.ar.domain

import kotlin.math.abs

/** Углы обзора камеры, градусы. Берутся из характеристик камеры устройства. */
data class CameraFieldOfView(
    val horizontalDegrees: Double,
    val verticalDegrees: Double,
) {
    companion object {
        /** Разумное значение для основной камеры телефона, если запросить не удалось. */
        val Default = CameraFieldOfView(horizontalDegrees = 66.0, verticalDegrees = 50.0)
    }
}

/** Куда смотрит устройство: азимут от истинного севера и наклон к горизонту. */
data class DeviceOrientation(
    val azimuthDegrees: Double,
    val pitchDegrees: Double,
)

/**
 * Положение метки в кадре.
 *
 * Координаты — доли от ширины и высоты (0..1), считая от левого верхнего угла.
 * Значения вне диапазона означают, что цель за кадром: по ним рисуется стрелка
 * «поверни туда», поэтому они не обрезаются.
 */
data class ScreenPosition(
    val xFraction: Float,
    val yFraction: Float,
    val onScreen: Boolean,
    /** Насколько повернуть устройство до цели по горизонтали, градусы. */
    val horizontalOffsetDegrees: Double,
)

/**
 * Проецирует направление на цель в координаты кадра.
 *
 * Модель намеренно простая — гномоническая проекция заменена линейной по углу.
 * На углах обзора телефона (60–70°) расхождение у краёв кадра порядка процента
 * ширины, что меньше дрожания самого компаса.
 */
fun projectToScreen(
    orientation: DeviceOrientation,
    targetBearingDegrees: Double,
    targetElevationDegrees: Double,
    fieldOfView: CameraFieldOfView = CameraFieldOfView.Default,
): ScreenPosition {
    val horizontalOffset = angleDeltaDegrees(orientation.azimuthDegrees, targetBearingDegrees)
    val verticalOffset = targetElevationDegrees - orientation.pitchDegrees

    val x = 0.5 + horizontalOffset / fieldOfView.horizontalDegrees
    val y = 0.5 - verticalOffset / fieldOfView.verticalDegrees

    return ScreenPosition(
        xFraction = x.toFloat(),
        yFraction = y.toFloat(),
        onScreen = x in 0.0..1.0 && y in 0.0..1.0,
        horizontalOffsetDegrees = horizontalOffset,
    )
}

/** С какой стороны кадра подсказывать поворот, когда цель не видна. */
enum class OffScreenHint { NONE, LEFT, RIGHT }

fun offScreenHint(position: ScreenPosition): OffScreenHint = when {
    position.onScreen -> OffScreenHint.NONE
    position.horizontalOffsetDegrees < 0 -> OffScreenHint.LEFT
    else -> OffScreenHint.RIGHT
}

/** Насколько пользователь «навёлся» на цель: 1.0 — точно в центре. */
fun aimAccuracy(position: ScreenPosition, toleranceDegrees: Double = 12.0): Float {
    val offset = abs(position.horizontalOffsetDegrees)
    if (offset >= toleranceDegrees) return 0f
    return (1.0 - offset / toleranceDegrees).toFloat()
}
