package ru.marshruty.ar.domain

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class ProjectionTest {

    private val fov = CameraFieldOfView(horizontalDegrees = 66.0, verticalDegrees = 50.0)

    private fun looking(azimuth: Double, pitch: Double = 0.0) =
        DeviceOrientation(azimuthDegrees = azimuth, pitchDegrees = pitch)

    @Test
    fun `цель строго по курсу попадает в центр кадра`() {
        val position = projectToScreen(looking(90.0), targetBearingDegrees = 90.0, targetElevationDegrees = 0.0, fieldOfView = fov)

        assertEquals(0.5f, position.xFraction, 0.001f)
        assertEquals(0.5f, position.yFraction, 0.001f)
        assertTrue(position.onScreen)
    }

    @Test
    fun `цель на половине угла обзора попадает на край кадра`() {
        val position = projectToScreen(looking(0.0), targetBearingDegrees = 33.0, targetElevationDegrees = 0.0, fieldOfView = fov)

        assertEquals(1.0f, position.xFraction, 0.001f)
        assertTrue(position.onScreen)
    }

    @Test
    fun `цель выше горизонта уходит к верху кадра`() {
        val position = projectToScreen(looking(0.0), targetBearingDegrees = 0.0, targetElevationDegrees = 25.0, fieldOfView = fov)

        assertEquals(0.0f, position.yFraction, 0.001f)
    }

    @Test
    fun `наклон устройства вверх опускает цель в кадре`() {
        val level = projectToScreen(looking(0.0, pitch = 0.0), 0.0, 0.0, fov)
        val tilted = projectToScreen(looking(0.0, pitch = 10.0), 0.0, 0.0, fov)

        assertTrue("при наклоне вверх цель должна уйти ниже", tilted.yFraction > level.yFraction)
    }

    @Test
    fun `цель за спиной считается вне кадра`() {
        val position = projectToScreen(looking(0.0), targetBearingDegrees = 180.0, targetElevationDegrees = 0.0, fieldOfView = fov)

        assertFalse(position.onScreen)
    }

    @Test
    fun `проекция корректно проходит через ноль градусов`() {
        // Смотрим почти на север, цель чуть правее нуля — метка обязана быть справа от центра.
        val position = projectToScreen(looking(355.0), targetBearingDegrees = 5.0, targetElevationDegrees = 0.0, fieldOfView = fov)

        assertTrue("ожидали смещение вправо, получили ${position.xFraction}", position.xFraction > 0.5f)
        assertEquals(10.0, position.horizontalOffsetDegrees, 0.001)
    }

    @Test
    fun `подсказка указывает сторону поворота`() {
        val toTheRight = projectToScreen(looking(0.0), 120.0, 0.0, fov)
        val toTheLeft = projectToScreen(looking(0.0), 240.0, 0.0, fov)
        val inFront = projectToScreen(looking(0.0), 0.0, 0.0, fov)

        assertEquals(OffScreenHint.RIGHT, offScreenHint(toTheRight))
        assertEquals(OffScreenHint.LEFT, offScreenHint(toTheLeft))
        assertEquals(OffScreenHint.NONE, offScreenHint(inFront))
    }

    @Test
    fun `точность наведения максимальна в центре и падает до нуля на границе допуска`() {
        val centered = projectToScreen(looking(0.0), 0.0, 0.0, fov)
        val half = projectToScreen(looking(0.0), 6.0, 0.0, fov)
        val outside = projectToScreen(looking(0.0), 20.0, 0.0, fov)

        assertEquals(1.0f, aimAccuracy(centered, toleranceDegrees = 12.0), 0.001f)
        assertEquals(0.5f, aimAccuracy(half, toleranceDegrees = 12.0), 0.001f)
        assertEquals(0.0f, aimAccuracy(outside, toleranceDegrees = 12.0), 0.001f)
    }

    @Test
    fun `точность наведения не зависит от знака отклонения`() {
        val left = projectToScreen(looking(0.0), 354.0, 0.0, fov)
        val right = projectToScreen(looking(0.0), 6.0, 0.0, fov)

        assertEquals(aimAccuracy(left), aimAccuracy(right), 0.001f)
    }
}
