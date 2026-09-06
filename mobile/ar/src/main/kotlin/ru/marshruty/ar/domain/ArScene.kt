package ru.marshruty.ar.domain

/** Насколько пользователь близко к точке маршрута. */
enum class Proximity {
    /** Далеко: показываем стрелку направления и расстояние. */
    FAR,

    /** Рядом: цель уже можно найти глазами. */
    NEAR,

    /** Пришёл: точку можно засчитать. */
    ARRIVED,
}

/**
 * Пороги подхода к точке, метры.
 *
 * `arrived` намеренно щедрый: бытовой GPS в лесу даёт разброс 5–15 м, и слишком
 * строгий радиус означает, что до точки «не дойти» при том, что человек стоит
 * ровно на ней.
 */
data class ProximityThresholds(
    val arrivedMeters: Double = 20.0,
    val nearMeters: Double = 60.0,
) {
    companion object {
        val Default = ProximityThresholds()
    }
}

fun proximityOf(
    distanceMeters: Double,
    thresholds: ProximityThresholds = ProximityThresholds.Default,
): Proximity = when {
    distanceMeters <= thresholds.arrivedMeters -> Proximity.ARRIVED
    distanceMeters <= thresholds.nearMeters -> Proximity.NEAR
    else -> Proximity.FAR
}

/** Точность позиционирования, по которой решаем, можно ли доверять наведению. */
data class LocationFix(
    val point: GeoPoint,
    val accuracyMeters: Double,
)

/**
 * Всё, что нужно нарисовать поверх кадра. Считается из сырых данных датчиков
 * без обращения к Android API, поэтому проверяется обычными unit-тестами.
 */
data class ArSceneState(
    val orientation: DeviceOrientation,
    val distanceMeters: Double?,
    val proximity: Proximity?,
    val markerPosition: ScreenPosition?,
    val offScreenHint: OffScreenHint,
    val aimAccuracy: Float,
    /** Заявленный разброс позиции, метры. null — фикса ещё нет. */
    val locationAccuracyMeters: Double?,
    /** Достоверность гео недостаточна — метку показывать нельзя. */
    val locationUnreliable: Boolean,
) {
    companion object {
        /** Хуже этого разброса наведение по компасу бессмысленно. */
        const val MAX_USABLE_ACCURACY_METERS = 40.0
    }
}

/**
 * Собирает состояние сцены.
 *
 * @param target цель наведения; null — сюжетная точка без привязки к местности,
 *   тогда рисуется только персонаж и субтитры.
 * @param targetHeightOffsetMeters превышение цели над наблюдателем.
 */
fun buildSceneState(
    fix: LocationFix?,
    orientation: DeviceOrientation,
    target: GeoPoint?,
    targetHeightOffsetMeters: Double = 0.0,
    fieldOfView: CameraFieldOfView = CameraFieldOfView.Default,
    thresholds: ProximityThresholds = ProximityThresholds.Default,
): ArSceneState {
    if (fix == null || target == null) {
        return ArSceneState(
            orientation = orientation,
            distanceMeters = null,
            proximity = null,
            markerPosition = null,
            offScreenHint = OffScreenHint.NONE,
            aimAccuracy = 0f,
            locationAccuracyMeters = fix?.accuracyMeters,
            locationUnreliable = fix == null && target != null,
        )
    }

    val unreliable = fix.accuracyMeters > ArSceneState.MAX_USABLE_ACCURACY_METERS
    val distance = distanceMeters(fix.point, target)
    val bearing = bearingDegrees(fix.point, target)
    val elevation = elevationDegrees(distance, targetHeightOffsetMeters)
    val position = projectToScreen(orientation, bearing, elevation, fieldOfView)

    return ArSceneState(
        orientation = orientation,
        distanceMeters = distance,
        proximity = proximityOf(distance, thresholds),
        markerPosition = if (unreliable) null else position,
        offScreenHint = if (unreliable) OffScreenHint.NONE else offScreenHint(position),
        aimAccuracy = if (unreliable) 0f else aimAccuracy(position),
        locationAccuracyMeters = fix.accuracyMeters,
        locationUnreliable = unreliable,
    )
}
