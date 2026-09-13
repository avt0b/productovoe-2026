package ru.marshruty.ar.domain

import kotlin.math.PI
import kotlin.math.sin

/**
 * Преобразование персонажа в момент сальто.
 *
 * Сальто как трансформация, а не как покадровая анимация: персонаж плоский и
 * приклеен к нижней трети кадра, поэтому поворот с подскоком читается так же,
 * как отрисованная последовательность, но работает с любым ассетом — хоть с
 * заглушкой, хоть с готовой моделью, — и не требует рисовать 24 кадра.
 *
 * Если для [CompanionAction.TRICK] всё-таки положат кадры, эта трансформация
 * не применяется: иначе персонаж крутанётся дважды.
 */
data class FlipTransform(
    /** Поворот вокруг центра, градусы. Отрицательный — назад, как в сальто. */
    val rotationDegrees: Float,
    /** Высота подскока в долях от заданной амплитуды: 0 на земле, 1 в верхней точке. */
    val liftFraction: Float,
    val scaleX: Float,
    val scaleY: Float,
)

/** Доля клипа на присед перед прыжком. */
private const val CROUCH_END = 0.16f

/** Доля клипа на полёт; остаток — приземление. */
private const val FLIGHT_END = 0.84f

/**
 * Состояние сальто на момент [progress] в диапазоне 0..1.
 *
 * Присед и приземление заданы полуволной синуса, а не линейно: так они равны
 * нулю на границах фаз, и масштаб не «щёлкает» при переходе присед → полёт →
 * земля. Растяжение в полёте противоположно приседу — это классическая
 * связка squash & stretch, без неё прыжок выглядит как поворот картинки.
 */
fun flipTransform(progress: Float): FlipTransform {
    val p = progress.coerceIn(0f, 1f)

    val crouch = if (p < CROUCH_END) halfWave(p / CROUCH_END) else 0f
    val land = if (p > FLIGHT_END) halfWave((p - FLIGHT_END) / (1f - FLIGHT_END)) else 0f
    val flight = if (p in CROUCH_END..FLIGHT_END) (p - CROUCH_END) / (FLIGHT_END - CROUCH_END) else 0f
    val lift = if (p in CROUCH_END..FLIGHT_END) halfWave(flight) else 0f

    val rotation = when {
        p < CROUCH_END -> 0f
        p > FLIGHT_END -> -360f
        else -> -360f * flight
    }

    return FlipTransform(
        rotationDegrees = rotation,
        liftFraction = lift,
        scaleX = 1f + 0.16f * crouch + 0.14f * land - 0.06f * lift,
        scaleY = 1f - 0.22f * crouch - 0.18f * land + 0.10f * lift,
    )
}

/** Полуволна синуса: 0 → 1 → 0. */
private fun halfWave(k: Float): Float = sin(PI * k.coerceIn(0f, 1f)).toFloat()
