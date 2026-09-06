package ru.marshruty.ar.domain

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class OpticsTest {

    // Типичная основная камера телефона: фокусное 4.3 мм, матрица 5.6 × 4.2 мм.
    private val focal = 4.3f
    private val sensorWidth = 5.6f
    private val sensorHeight = 4.2f

    @Test
    fun `в альбомной ориентации по горизонтали идёт длинная сторона матрицы`() {
        val fov = fieldOfViewFrom(focal, sensorWidth, sensorHeight, portrait = false)

        assertEquals(66.1, fov.horizontalDegrees, 0.3)
        assertEquals(52.1, fov.verticalDegrees, 0.3)
    }

    @Test
    fun `в портретной ориентации стороны меняются местами`() {
        val fov = fieldOfViewFrom(focal, sensorWidth, sensorHeight, portrait = true)

        assertEquals(52.1, fov.horizontalDegrees, 0.3)
        assertEquals(66.1, fov.verticalDegrees, 0.3)
    }

    @Test
    fun `перепутанная ориентация даёт ошибку почти в полтора раза`() {
        val portrait = fieldOfViewFrom(focal, sensorWidth, sensorHeight, portrait = true)
        val landscape = fieldOfViewFrom(focal, sensorWidth, sensorHeight, portrait = false)

        // Это не придирка: 14 градусов разницы — четверть ширины кадра.
        assertTrue(landscape.horizontalDegrees - portrait.horizontalDegrees > 12.0)
    }

    @Test
    fun `длиннофокусный объектив сужает угол обзора`() {
        val wide = fieldOfViewFrom(focalLengthMm = 2.2f, sensorWidthMm = sensorWidth, sensorHeightMm = sensorHeight)
        val tele = fieldOfViewFrom(focalLengthMm = 12.0f, sensorWidthMm = sensorWidth, sensorHeightMm = sensorHeight)

        assertTrue(wide.horizontalDegrees > tele.horizontalDegrees)
        assertTrue("телевик должен быть заметно уже", tele.horizontalDegrees < 25.0)
    }

    @Test
    fun `значение по умолчанию близко к типичной камере телефона`() {
        val typical = fieldOfViewFrom(focal, sensorWidth, sensorHeight, portrait = false)

        assertEquals(CameraFieldOfView.Default.horizontalDegrees, typical.horizontalDegrees, 1.0)
    }

    @Test(expected = IllegalArgumentException::class)
    fun `нулевое фокусное расстояние отвергается`() {
        fieldOfViewFrom(focalLengthMm = 0f, sensorWidthMm = 5.6f, sensorHeightMm = 4.2f)
    }

    @Test(expected = IllegalArgumentException::class)
    fun `нулевой размер матрицы отвергается`() {
        fieldOfViewFrom(focalLengthMm = 4.3f, sensorWidthMm = 0f, sensorHeightMm = 4.2f)
    }
}
