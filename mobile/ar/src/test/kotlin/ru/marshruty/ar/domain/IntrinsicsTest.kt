package ru.marshruty.ar.domain

import org.junit.Assert.assertEquals
import org.junit.Test
import kotlin.math.atan

class IntrinsicsTest {

    private fun angle(size: Double, focal: Double) = Math.toDegrees(2.0 * atan(size / 2.0 / focal))

    @Test
    fun `в портрете короткая сторона кадра идёт поперёк экрана`() {
        val fov = fieldOfViewFromIntrinsics(focalX = 1500f, focalY = 1500f, width = 1920, height = 1080)
        assertEquals(angle(1080.0, 1500.0), fov.horizontalDegrees, EPS)
        assertEquals(angle(1920.0, 1500.0), fov.verticalDegrees, EPS)
    }

    @Test
    fun `в альбомной ориентации оси не меняются`() {
        val fov = fieldOfViewFromIntrinsics(1500f, 1500f, 1920, 1080, portrait = false)
        assertEquals(angle(1920.0, 1500.0), fov.horizontalDegrees, EPS)
        assertEquals(angle(1080.0, 1500.0), fov.verticalDegrees, EPS)
    }

    @Test
    fun `каждое фокусное расстояние относится к своей оси`() {
        // Неквадратные пиксели: fx к ширине, fy к высоте — перепутать их значит
        // ошибиться с углом на всю разницу фокусных.
        val fov = fieldOfViewFromIntrinsics(focalX = 1400f, focalY = 1600f, width = 1920, height = 1080)
        assertEquals(angle(1080.0, 1600.0), fov.horizontalDegrees, EPS)
        assertEquals(angle(1920.0, 1400.0), fov.verticalDegrees, EPS)
    }

    @Test
    fun `кадр, отданный уже в портретной ориентации, даёт тот же угол`() {
        val landscape = fieldOfViewFromIntrinsics(1400f, 1600f, 1920, 1080)
        val portrait = fieldOfViewFromIntrinsics(1600f, 1400f, 1080, 1920)
        assertEquals(landscape.horizontalDegrees, portrait.horizontalDegrees, EPS)
        assertEquals(landscape.verticalDegrees, portrait.verticalDegrees, EPS)
    }

    @Test
    fun `совпадает с расчётом по миллиметрам матрицы`() {
        // Матрица 6.4×3.6 мм на 1920×1080 пикселей: шаг 1/300 мм. Объектив 4 мм —
        // это 1200 пикселей. Два пути к одному углу обязаны сойтись.
        val fromMillimeters = fieldOfViewFrom(focalLengthMm = 4f, sensorWidthMm = 6.4f, sensorHeightMm = 3.6f)
        val fromPixels = fieldOfViewFromIntrinsics(focalX = 1200f, focalY = 1200f, width = 1920, height = 1080)
        assertEquals(fromMillimeters.horizontalDegrees, fromPixels.horizontalDegrees, 1e-3)
        assertEquals(fromMillimeters.verticalDegrees, fromPixels.verticalDegrees, 1e-3)
    }

    @Test(expected = IllegalArgumentException::class)
    fun `нулевое фокусное расстояние отвергается`() {
        fieldOfViewFromIntrinsics(0f, 1500f, 1920, 1080)
    }

    private companion object {
        const val EPS = 1e-6
    }
}
