package ru.marshruty.ar.domain

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test
import kotlin.math.abs

class OrientationFilterTest {

    @Test
    fun `первое значение принимается как есть`() {
        val filter = OrientationFilter(smoothing = 0.2)

        assertEquals(42.0, filter.update(42.0), 0.001)
    }

    @Test
    fun `до первого отсчёта текущего значения нет`() {
        assertNull(OrientationFilter().current)
    }

    @Test
    fun `фильтр сходится к постоянному входу`() {
        val filter = OrientationFilter(smoothing = 0.3)
        filter.update(0.0)
        repeat(100) { filter.update(90.0) }

        assertEquals(90.0, filter.current!!, 0.01)
    }

    @Test
    fun `переход через ноль идёт кратчайшей дугой а не через всю окружность`() {
        val filter = OrientationFilter(smoothing = 0.5)
        filter.update(350.0)
        val next = filter.update(10.0)

        // Кратчайший путь 350 -> 10 это +20 градусов, середина — 0.
        assertEquals(0.0, angleDeltaDegrees(0.0, next), 0.001)
    }

    @Test
    fun `результат всегда остаётся в диапазоне 0-360`() {
        val filter = OrientationFilter(smoothing = 0.4)
        val inputs = listOf(350.0, 5.0, 355.0, 15.0, 300.0, 60.0, 0.0, 359.9)

        inputs.forEach { raw ->
            val value = filter.update(raw)
            assertTrue("значение $value вне диапазона", value >= 0.0 && value < 360.0)
        }
    }

    @Test
    fun `дрожание входа сглаживается сильнее при меньшем коэффициенте`() {
        val noisy = listOf(100.0, 104.0, 96.0, 103.0, 97.0, 102.0, 98.0, 101.0)

        fun spread(smoothing: Double): Double {
            val filter = OrientationFilter(smoothing)
            val output = noisy.map { filter.update(it) }
            // Первое значение принимается как есть — оно не характеризует сглаживание.
            val tail = output.drop(1)
            return tail.max() - tail.min()
        }

        assertTrue("мягкий фильтр должен давать меньший разброс", spread(0.1) < spread(0.6))
    }

    @Test
    fun `сброс возвращает фильтр в исходное состояние`() {
        val filter = OrientationFilter()
        filter.update(120.0)
        filter.reset()

        assertNull(filter.current)
        assertEquals(7.0, filter.update(7.0), 0.001)
    }

    @Test
    fun `фильтр не отстаёт навсегда при медленном повороте`() {
        val filter = OrientationFilter(smoothing = 0.25)
        filter.update(0.0)
        // Имитируем плавный поворот на 60 градусов по одному градусу за отсчёт.
        for (degree in 1..60) filter.update(degree.toDouble())

        val lag = abs(angleDeltaDegrees(filter.current!!, 60.0))
        assertTrue("отставание $lag градусов слишком велико", lag < 4.0)
    }

    @Test(expected = IllegalArgumentException::class)
    fun `недопустимый коэффициент сглаживания отвергается`() {
        OrientationFilter(smoothing = 0.0)
    }
}
