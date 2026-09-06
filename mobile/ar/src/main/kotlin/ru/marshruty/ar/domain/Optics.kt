package ru.marshruty.ar.domain

import kotlin.math.atan
import kotlin.math.tan

/**
 * Углы обзора камеры из характеристик объектива.
 *
 * Значение по умолчанию (66°) — усреднённое, и на конкретном телефоне метка
 * из-за него промахивается на несколько градусов. Реальные фокусное расстояние
 * и размер матрицы даёт Camera2 (`LENS_INFO_AVAILABLE_FOCAL_LENGTHS`,
 * `SENSOR_INFO_PHYSICAL_SIZE`), а перевод в углы — здесь, чтобы его можно было
 * проверить тестом.
 *
 * @param portrait экран держат вертикально. Матрица описывается в альбомной
 *   системе, поэтому по горизонтали экрана оказывается её **короткая** сторона.
 *   Перепутать местами — значит ошибиться в углах почти вдвое.
 */
fun fieldOfViewFrom(
    focalLengthMm: Float,
    sensorWidthMm: Float,
    sensorHeightMm: Float,
    portrait: Boolean = true,
): CameraFieldOfView {
    require(focalLengthMm > 0f) { "Фокусное расстояние должно быть положительным" }
    require(sensorWidthMm > 0f && sensorHeightMm > 0f) { "Размер матрицы должен быть положительным" }

    val across = if (portrait) sensorHeightMm else sensorWidthMm
    val along = if (portrait) sensorWidthMm else sensorHeightMm

    return CameraFieldOfView(
        horizontalDegrees = viewAngleDegrees(across, focalLengthMm),
        verticalDegrees = viewAngleDegrees(along, focalLengthMm),
    )
}

private fun viewAngleDegrees(sensorDimensionMm: Float, focalLengthMm: Float): Double =
    Math.toDegrees(2.0 * atan(sensorDimensionMm / (2.0 * focalLengthMm)))

/**
 * Поправка углов обзора на кадрирование превью.
 *
 * `PreviewView` в режиме FILL_CENTER растягивает кадр на весь экран и обрезает
 * лишнее. Матрица при этом по-прежнему заявляет свои углы, но видно уже меньше —
 * и метка, посчитанная по «паспортным» углам, уезжает от цели. Разница на
 * телефоне с экраном 20:9 и кадром 4:3 доходит до трети ширины.
 *
 * @param viewAspectRatio ширина/высота области показа.
 * @param frameAspectRatio ширина/высота кадра, приходящего с камеры.
 */
fun croppedFieldOfView(
    full: CameraFieldOfView,
    viewAspectRatio: Double,
    frameAspectRatio: Double,
): CameraFieldOfView {
    require(viewAspectRatio > 0.0 && frameAspectRatio > 0.0) { "Соотношение сторон должно быть положительным" }

    val halfWidth = tan(Math.toRadians(full.horizontalDegrees / 2.0))
    val halfHeight = tan(Math.toRadians(full.verticalDegrees / 2.0))

    return if (viewAspectRatio > frameAspectRatio) {
        // Область показа шире кадра: по ширине сходится, по высоте обрезано.
        val kept = frameAspectRatio / viewAspectRatio
        CameraFieldOfView(
            horizontalDegrees = full.horizontalDegrees,
            verticalDegrees = Math.toDegrees(2.0 * atan(halfHeight * kept)),
        )
    } else {
        val kept = viewAspectRatio / frameAspectRatio
        CameraFieldOfView(
            horizontalDegrees = Math.toDegrees(2.0 * atan(halfWidth * kept)),
            verticalDegrees = full.verticalDegrees,
        )
    }
}
