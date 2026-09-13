package ru.marshruty.ar.ui

import org.junit.Assert.assertEquals
import org.junit.Test

class MarkerDecodeTest {

    @Test
    fun `маркер из генератора уменьшается вдвое`() {
        // 1600×1100 → 800×550: вчетверо меньше пикселей на попиксельный перевод в серое.
        assertEquals(2, sampleSizeFor(width = 1600, height = 1100, maxSide = 800))
    }

    @Test
    fun `картинка уже нужного размера не трогается`() {
        assertEquals(1, sampleSizeFor(width = 800, height = 550, maxSide = 800))
        assertEquals(1, sampleSizeFor(width = 700, height = 700, maxSide = 800))
    }

    @Test
    fun `большая сторона не становится меньше порога`() {
        // Фото с телефона 4000×3000: делитель 4 даёт 1000, делитель 8 — уже 500.
        assertEquals(4, sampleSizeFor(width = 4000, height = 3000, maxSide = 800))
    }

    @Test
    fun `портретная картинка считается по высоте`() {
        assertEquals(2, sampleSizeFor(width = 1100, height = 1600, maxSide = 800))
    }

    @Test
    fun `нулевые размеры не зацикливают расчёт`() {
        assertEquals(1, sampleSizeFor(width = 0, height = 0, maxSide = 800))
    }
}
