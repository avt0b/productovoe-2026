package ru.marshruty.ar.domain

/**
 * Сглаживание показаний компаса.
 *
 * Сырой азимут с телефона дрожит на несколько градусов даже в покое — метка
 * без фильтра вибрирует и читается как баг. Фильтр экспоненциальный и работает
 * по кратчайшей дуге, поэтому корректно проходит через 0°/360°.
 *
 * @param smoothing доля нового значения на шаг: меньше — плавнее, но с задержкой.
 */
class OrientationFilter(private val smoothing: Double = 0.15) {

    init {
        require(smoothing > 0.0 && smoothing <= 1.0) { "smoothing должен быть в (0, 1]" }
    }

    private var value: Double? = null

    /** Текущее сглаженное значение или null, пока не пришло ни одного отсчёта. */
    val current: Double? get() = value

    fun update(rawDegrees: Double): Double {
        val previous = value
        val next = if (previous == null) {
            normalizeDegrees(rawDegrees)
        } else {
            normalizeDegrees(previous + smoothing * angleDeltaDegrees(previous, rawDegrees))
        }
        value = next
        return next
    }

    /** Сбрасывает состояние — например, после перекалибровки компаса. */
    fun reset() {
        value = null
    }
}
