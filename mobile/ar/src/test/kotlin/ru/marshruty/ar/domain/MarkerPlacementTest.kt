package ru.marshruty.ar.domain

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test
import kotlin.math.cos
import kotlin.math.sin

class MarkerPlacementTest {

    /** Картинка на столе: нормаль вверх, низ картинки смотрит на +Z. */
    private val onTable = MarkerPose(
        center = Vec3(0.2, 0.75, -0.5),
        normal = Vec3(0.0, 1.0, 0.0),
        towardBottom = Vec3(0.0, 0.0, 1.0),
        heightMeters = 0.21,
    )

    /** Табличка на стене: нормаль к +Z, низ смотрит в пол. */
    private val onWall = MarkerPose(
        center = Vec3(0.0, 1.5, -2.0),
        normal = Vec3(0.0, 0.0, 1.0),
        towardBottom = Vec3(0.0, -1.0, 0.0),
        heightMeters = 0.4,
    )

    @Test
    fun `на столе проводник стоит прямо на картинке`() {
        val placement = placeCompanion(onTable, camera = Vec3(0.2, 1.3, 0.1))
        assertEquals(MarkerOrientation.LYING, placement.orientation)
        assertVec(onTable.center, placement.position)
    }

    @Test
    fun `на стене проводник стоит у нижнего края и не проваливается в стену`() {
        val placement = placeCompanion(onWall, camera = Vec3(0.0, 1.6, 0.0))
        assertEquals(MarkerOrientation.STANDING, placement.orientation)
        assertEquals("высота — нижний край таблички", 1.3, placement.position.y, EPS)
        assertTrue("стоит перед плоскостью стены", placement.position.z > onWall.center.z)
        assertEquals(onWall.center.x, placement.position.x, EPS)
    }

    @Test
    fun `проводник поворачивается лицом к камере`() {
        val atOrigin = onTable.copy(center = Vec3(0.0, 0.0, 0.0))
        assertEquals(0.0, placeCompanion(atOrigin, Vec3(0.0, 1.0, 2.0)).yawDegrees, EPS)
        assertEquals(90.0, placeCompanion(atOrigin, Vec3(2.0, 1.0, 0.0)).yawDegrees, EPS)
        assertEquals(180.0, placeCompanion(atOrigin, Vec3(0.0, 1.0, -2.0)).yawDegrees, EPS)
        assertEquals(270.0, placeCompanion(atOrigin, Vec3(-2.0, 1.0, 0.0)).yawDegrees, EPS)
    }

    @Test
    fun `высота камеры на поворот не влияет`() {
        // Смотрим сверху или снизу — персонаж не должен запрокидываться или крениться.
        val low = placeCompanion(onTable, Vec3(1.2, 0.8, 0.5)).yawDegrees
        val high = placeCompanion(onTable, Vec3(1.2, 3.0, 0.5)).yawDegrees
        assertEquals(low, high, EPS)
    }

    @Test
    fun `камера прямо сверху — лицом к нижнему краю картинки`() {
        val placement = placeCompanion(onTable, camera = onTable.center + Vec3(0.0, 0.6, 0.0))
        assertEquals(0.0, placement.yawDegrees, EPS)
    }

    @Test
    fun `наклон до 45 градусов — картинка лежит, круче — висит`() {
        fun tilted(degrees: Double) = onTable.copy(
            normal = Vec3(0.0, cos(Math.toRadians(degrees)), sin(Math.toRadians(degrees))),
        )
        assertEquals(MarkerOrientation.LYING, placeCompanion(tilted(30.0), Vec3(0.0, 2.0, 2.0)).orientation)
        assertEquals(MarkerOrientation.STANDING, placeCompanion(tilted(60.0), Vec3(0.0, 2.0, 2.0)).orientation)
    }

    @Test
    fun `направление без горизонтальной составляющей не определено`() {
        assertNull(yawToward(Vec3(0.0, 5.0, 0.0)))
    }

    @Test
    fun `без таблички проводник встаёт по лучу взгляда`() {
        val eye = Vec3(0.0, 1.5, 0.0)
        val pose = poseInFrontOfCamera(eye, forward = Vec3(0.0, 0.0, -1.0), distanceMeters = 0.8, companionHeightMeters = 0.3)
        assertVec(Vec3(0.0, 1.35, -0.8), pose.center)

        val placement = placeCompanion(pose, eye)
        assertEquals(MarkerOrientation.LYING, placement.orientation)
        assertEquals("лицом к человеку", 0.0, placement.yawDegrees, EPS)
    }

    @Test
    fun `телефон наклонён вниз — проводник ниже, а не над кадром`() {
        val eye = Vec3(0.0, 1.5, 0.0)
        val level = poseInFrontOfCamera(eye, Vec3(0.0, 0.0, -1.0), 0.8, 0.3)
        val tilted = poseInFrontOfCamera(eye, Vec3(0.0, -1.0, -1.0), 0.8, 0.3)
        assertTrue(tilted.center.y < level.center.y)
        assertEquals(0.8, (tilted.center + Vec3(0.0, 0.15, 0.0) - eye).length, EPS)
    }

    @Test
    fun `первый кадр сглаживания отдаётся как есть`() {
        val smoother = PlacementSmoother()
        val target = placement(Vec3(1.0, 0.0, 1.0), yaw = 40.0)
        assertEquals(target, smoother.update(target))
    }

    @Test
    fun `дрожь позы гасится`() {
        val smoother = PlacementSmoother(positionFactor = 0.25)
        smoother.update(placement(Vec3(0.0, 0.0, 0.0), yaw = 0.0))
        val next = smoother.update(placement(Vec3(0.01, 0.0, 0.0), yaw = 0.0))
        assertEquals("сдвиг на сантиметр прошёл на четверть", 0.0025, next.position.x, EPS)
    }

    @Test
    fun `переставленный маркер не ползёт через стол`() {
        val smoother = PlacementSmoother(jumpMeters = 0.5)
        smoother.update(placement(Vec3(0.0, 0.0, 0.0), yaw = 0.0))
        val far = placement(Vec3(0.8, 0.0, 0.0), yaw = 0.0)
        assertEquals(far, smoother.update(far))
    }

    @Test
    fun `поворот идёт коротким путём через ноль`() {
        val smoother = PlacementSmoother(yawFactor = 0.5)
        smoother.update(placement(Vec3(0.0, 0.0, 0.0), yaw = 350.0))
        val next = smoother.update(placement(Vec3(0.0, 0.0, 0.0), yaw = 10.0))
        // Через 0: 350 → 0, а не 350 → 180 → 10.
        assertEquals(0.0, next.yawDegrees, EPS)
    }

    @Test
    fun `после сброса поза снова берётся как есть`() {
        val smoother = PlacementSmoother()
        smoother.update(placement(Vec3(0.0, 0.0, 0.0), yaw = 0.0))
        smoother.reset()
        val target = placement(Vec3(0.1, 0.0, 0.0), yaw = 90.0)
        assertEquals(target, smoother.update(target))
    }

    private fun placement(position: Vec3, yaw: Double) =
        CompanionPlacement(position, yaw, MarkerOrientation.LYING)

    private fun assertVec(expected: Vec3, actual: Vec3) {
        assertEquals("x", expected.x, actual.x, EPS)
        assertEquals("y", expected.y, actual.y, EPS)
        assertEquals("z", expected.z, actual.z, EPS)
    }

    private companion object {
        const val EPS = 1e-6
    }
}
