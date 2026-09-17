package ru.marshruty.ar.domain

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class ArSceneTest {

    private val observer = GeoPoint(52.9700, 36.0670)
    private val northOfObserver = GeoPoint(52.9705, 36.0670) // ~55 м на север
    private val orientation = DeviceOrientation(azimuthDegrees = 0.0, pitchDegrees = 0.0)

    private fun fix(accuracy: Double = 8.0, at: GeoPoint = observer) =
        LocationFix(point = at, accuracyMeters = accuracy)

    @Test
    fun `подход к точке проходит три стадии`() {
        assertEquals(Proximity.ARRIVED, proximityOf(5.0))
        assertEquals(Proximity.NEAR, proximityOf(40.0))
        assertEquals(Proximity.FAR, proximityOf(400.0))
    }

    @Test
    fun `границы порогов включаются в ближнюю стадию`() {
        val thresholds = ProximityThresholds(arrivedMeters = 20.0, nearMeters = 60.0)

        assertEquals(Proximity.ARRIVED, proximityOf(20.0, thresholds))
        assertEquals(Proximity.NEAR, proximityOf(20.001, thresholds))
        assertEquals(Proximity.NEAR, proximityOf(60.0, thresholds))
        assertEquals(Proximity.FAR, proximityOf(60.001, thresholds))
    }

    @Test
    fun `цель на севере при взгляде на север оказывается в центре кадра`() {
        val state = buildSceneState(fix(), orientation, northOfObserver)

        assertNotNull(state.markerPosition)
        assertEquals(0.5f, state.markerPosition!!.xFraction, 0.02f)
        assertTrue(state.markerPosition!!.onScreen)
        assertEquals(1.0f, state.aimAccuracy, 0.05f)
    }

    @Test
    fun `дистанция считается и попадает в состояние`() {
        val state = buildSceneState(fix(), orientation, northOfObserver)

        assertNotNull(state.distanceMeters)
        assertEquals(55.0, state.distanceMeters!!, 10.0)
        assertEquals(Proximity.NEAR, state.proximity)
    }

    @Test
    fun `при взгляде в другую сторону метка уходит за кадр и появляется подсказка`() {
        val lookingSouth = DeviceOrientation(azimuthDegrees = 180.0, pitchDegrees = 0.0)
        val state = buildSceneState(fix(), lookingSouth, northOfObserver)

        assertFalse(state.markerPosition!!.onScreen)
        assertTrue(state.offScreenHint != OffScreenHint.NONE)
        assertEquals(0f, state.aimAccuracy, 0.001f)
    }

    @Test
    fun `плохая точность гео прячет метку вместо того чтобы врать`() {
        val state = buildSceneState(fix(accuracy = 120.0), orientation, northOfObserver)

        assertTrue(state.locationUnreliable)
        assertNull("метка при разбросе 120 м вводит в заблуждение", state.markerPosition)
        assertEquals(OffScreenHint.NONE, state.offScreenHint)
        // Дистанцию при этом всё равно показываем — она хоть и грубая, но полезная.
        assertNotNull(state.distanceMeters)
    }

    @Test
    fun `точка без гео-цели даёт сцену только с персонажем`() {
        val state = buildSceneState(fix(), orientation, target = null)

        assertNull(state.markerPosition)
        assertNull(state.distanceMeters)
        assertNull(state.proximity)
        assertFalse("это не ошибка гео, а сюжетная точка", state.locationUnreliable)
    }

    @Test
    fun `отсутствие фикса при наличии цели помечается как недостоверное гео`() {
        val state = buildSceneState(fix = null, orientation = orientation, target = northOfObserver)

        assertTrue(state.locationUnreliable)
        assertNull(state.markerPosition)
    }

    @Test
    fun `ориентация переносится в состояние без изменений`() {
        val custom = DeviceOrientation(azimuthDegrees = 137.5, pitchDegrees = -4.25)
        val state = buildSceneState(fix(), custom, northOfObserver)

        assertEquals(137.5, state.orientation.azimuthDegrees, 0.001)
        assertEquals(-4.25, state.orientation.pitchDegrees, 0.001)
    }
}
