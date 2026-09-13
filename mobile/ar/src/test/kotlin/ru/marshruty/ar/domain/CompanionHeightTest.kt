package ru.marshruty.ar.domain

import org.junit.Assert.assertEquals
import org.junit.Test

class CompanionHeightTest {

    @Test
    fun `явно заданный рост главнее всего`() {
        assertEquals(0.5f, companionHeightFor(explicitMeters = 0.5f, knownWidthMeters = 0.3f, measuredWidthMeters = 0.07f), EPS)
    }

    @Test
    fun `известная ширина таблички главнее измеренной`() {
        // Напечатанная табличка измерена рулеткой — точнее, чем оценка ARCore.
        assertEquals(0.33f, companionHeightFor(null, knownWidthMeters = 0.3f, measuredWidthMeters = 0.07f), EPS)
    }

    @Test
    fun `без ширины рост считается от измеренной`() {
        // Маркер на экране телефона шириной 6.5 см — проводник чуть выше него, а не в полметра.
        assertEquals(0.0715f, companionHeightFor(null, null, measuredWidthMeters = 0.065f), EPS)
    }

    @Test
    fun `до первого измерения берётся рост по умолчанию`() {
        assertEquals(DEFAULT_COMPANION_HEIGHT_METERS, companionHeightFor(null, null, null), EPS)
    }

    @Test
    fun `шум первых кадров не принимается за размер`() {
        assertEquals(DEFAULT_COMPANION_HEIGHT_METERS, companionHeightFor(null, null, measuredWidthMeters = 0.001f), EPS)
    }

    private companion object {
        const val EPS = 1e-5f
    }
}
