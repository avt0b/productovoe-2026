package ru.marshruty.ar.domain

import kotlin.math.asin
import kotlin.math.atan2
import kotlin.math.cos
import kotlin.math.min
import kotlin.math.pow
import kotlin.math.sin
import kotlin.math.sqrt

/** Точка на местности, градусы WGS-84. */
data class GeoPoint(val latitude: Double, val longitude: Double)

/** Средний радиус Земли (IUGG), метры. */
private const val EARTH_RADIUS_M = 6_371_008.8

/**
 * Расстояние по большому кругу, метры. Формула гаверсинуса.
 *
 * На дистанциях маршрута (сотни метров) погрешность сферической модели
 * относительно эллипсоида — сантиметры, для наведения камеры это неразличимо.
 */
fun distanceMeters(from: GeoPoint, to: GeoPoint): Double {
    val phi1 = Math.toRadians(from.latitude)
    val phi2 = Math.toRadians(to.latitude)
    val deltaPhi = Math.toRadians(to.latitude - from.latitude)
    val deltaLambda = Math.toRadians(to.longitude - from.longitude)

    val a = sin(deltaPhi / 2).pow(2) + cos(phi1) * cos(phi2) * sin(deltaLambda / 2).pow(2)
    return 2 * EARTH_RADIUS_M * asin(min(1.0, sqrt(a)))
}

/**
 * Начальный азимут на цель: 0..360 градусов от **истинного** севера по часовой.
 *
 * Датчик ориентации даёт азимут от магнитного севера, поэтому перед сравнением
 * его нужно поправить на магнитное склонение — см. [applyDeclination].
 */
fun bearingDegrees(from: GeoPoint, to: GeoPoint): Double {
    val phi1 = Math.toRadians(from.latitude)
    val phi2 = Math.toRadians(to.latitude)
    val deltaLambda = Math.toRadians(to.longitude - from.longitude)

    val y = sin(deltaLambda) * cos(phi2)
    val x = cos(phi1) * sin(phi2) - sin(phi1) * cos(phi2) * cos(deltaLambda)
    return normalizeDegrees(Math.toDegrees(atan2(y, x)))
}

/**
 * Магнитный азимут → истинный.
 *
 * В Орловской области склонение около +9°, и без поправки метка уезжает вбок
 * почти на треть ширины кадра. Значение берётся из `android.hardware.GeomagneticField`.
 */
fun applyDeclination(magneticAzimuth: Double, declinationDegrees: Double): Double =
    normalizeDegrees(magneticAzimuth + declinationDegrees)

/** Приводит угол к диапазону [0, 360). */
fun normalizeDegrees(degrees: Double): Double {
    val value = degrees % 360.0
    return if (value < 0) value + 360.0 else value
}

/**
 * Кратчайший поворот от одного азимута к другому, диапазон (-180, 180].
 * Отрицательное значение — цель левее, положительное — правее.
 */
fun angleDeltaDegrees(from: Double, to: Double): Double {
    val delta = normalizeDegrees(to - from + 180.0)
    return delta - 180.0
}

/**
 * Угол места цели относительно горизонта, градусы.
 *
 * Считаем плоско: на дистанциях до километра кривизна Земли даёт доли градуса,
 * а высоту цели мы всё равно знаем неточно.
 */
fun elevationDegrees(distanceMeters: Double, heightDifferenceMeters: Double): Double {
    if (distanceMeters <= 0.0) return 0.0
    return Math.toDegrees(atan2(heightDifferenceMeters, distanceMeters))
}
