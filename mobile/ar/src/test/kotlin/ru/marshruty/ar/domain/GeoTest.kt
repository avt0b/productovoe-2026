package ru.marshruty.ar.domain

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class GeoTest {

    private val orel = GeoPoint(52.9651, 36.0785)
    private val moscow = GeoPoint(55.7558, 37.6173)
    private val equator = GeoPoint(0.0, 0.0)

    @Test
    fun `расстояние до самой себя равно нулю`() {
        assertEquals(0.0, distanceMeters(orel, orel), 0.001)
    }

    @Test
    fun `один градус широты на экваторе — около 111 км`() {
        val distance = distanceMeters(equator, GeoPoint(1.0, 0.0))
        assertEquals(111_195.0, distance, 500.0)
    }

    @Test
    fun `Орёл — Москва около 326 км`() {
        val distance = distanceMeters(orel, moscow)
        assertEquals(326_000.0, distance, 2_000.0)
    }

    @Test
    fun `расстояние симметрично`() {
        assertEquals(distanceMeters(orel, moscow), distanceMeters(moscow, orel), 0.001)
    }

    @Test
    fun `азимут на север равен нулю`() {
        assertEquals(0.0, bearingDegrees(equator, GeoPoint(1.0, 0.0)), 0.01)
    }

    @Test
    fun `азимут на восток равен 90 градусам`() {
        assertEquals(90.0, bearingDegrees(equator, GeoPoint(0.0, 1.0)), 0.01)
    }

    @Test
    fun `азимут на юг равен 180 градусам`() {
        assertEquals(180.0, bearingDegrees(equator, GeoPoint(-1.0, 0.0)), 0.01)
    }

    @Test
    fun `азимут на запад равен 270 градусам`() {
        assertEquals(270.0, bearingDegrees(equator, GeoPoint(0.0, -1.0)), 0.01)
    }

    @Test
    fun `из Орла Москва примерно на северо-восток`() {
        val bearing = bearingDegrees(orel, moscow)
        assertTrue("ожидали сектор СВ, получили $bearing", bearing in 10.0..50.0)
    }

    @Test
    fun `нормализация приводит угол к диапазону 0-360`() {
        assertEquals(10.0, normalizeDegrees(370.0), 0.001)
        assertEquals(350.0, normalizeDegrees(-10.0), 0.001)
        assertEquals(0.0, normalizeDegrees(720.0), 0.001)
        assertEquals(180.0, normalizeDegrees(-180.0), 0.001)
    }

    @Test
    fun `разница углов идёт кратчайшей дугой через ноль`() {
        assertEquals(20.0, angleDeltaDegrees(350.0, 10.0), 0.001)
        assertEquals(-20.0, angleDeltaDegrees(10.0, 350.0), 0.001)
        assertEquals(0.0, angleDeltaDegrees(123.0, 123.0), 0.001)
    }

    @Test
    fun `разница углов не выходит за пределы 180 градусов`() {
        for (from in 0 until 360 step 7) {
            for (to in 0 until 360 step 11) {
                val delta = angleDeltaDegrees(from.toDouble(), to.toDouble())
                assertTrue("$from -> $to дало $delta", delta > -180.0001 && delta <= 180.0001)
            }
        }
    }

    @Test
    fun `магнитное склонение сдвигает азимут и остаётся в диапазоне`() {
        assertEquals(19.0, applyDeclination(10.0, 9.0), 0.001)
        assertEquals(4.0, applyDeclination(355.0, 9.0), 0.001)
        assertEquals(351.0, applyDeclination(0.0, -9.0), 0.001)
    }

    @Test
    fun `угол места положителен когда цель выше наблюдателя`() {
        assertEquals(45.0, elevationDegrees(distanceMeters = 10.0, heightDifferenceMeters = 10.0), 0.01)
        assertEquals(0.0, elevationDegrees(distanceMeters = 100.0, heightDifferenceMeters = 0.0), 0.01)
        assertTrue(elevationDegrees(100.0, -20.0) < 0.0)
    }

    @Test
    fun `угол места не делит на ноль на нулевой дистанции`() {
        assertEquals(0.0, elevationDegrees(distanceMeters = 0.0, heightDifferenceMeters = 5.0), 0.001)
    }
}
