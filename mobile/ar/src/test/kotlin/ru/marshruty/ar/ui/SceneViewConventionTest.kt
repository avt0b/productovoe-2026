package ru.marshruty.ar.ui

import dev.romainguy.kotlin.math.Float3
import dev.romainguy.kotlin.math.Float4
import dev.romainguy.kotlin.math.Quaternion
import dev.romainguy.kotlin.math.rotation
import org.junit.Assert.assertEquals
import org.junit.Test
import ru.marshruty.ar.domain.Vec3
import ru.marshruty.ar.domain.yawToward
import kotlin.math.hypot

/**
 * Соглашения SceneView о поворотах, на которые опирается ArMarkerScene.
 *
 * Node.rotation в SceneView — углы Эйлера в градусах, которые переводятся в
 * кватернион через kotlin-math Quaternion.fromEuler. Какое направление угла
 * положительное, там не написано, а ошибка в знаке на телефоне выглядит так:
 * спереди проводник смотрит на человека, а стоит зайти сбоку — отворачивается.
 * Тест держит поведение библиотеки: обновится SceneView и знак поменяется —
 * упадёт здесь, а не на показе.
 */
class SceneViewConventionTest {

    /** Ровно то, что делает Node: fromEuler, затем матрица поворота. */
    private fun rotate(euler: Float3, vector: Float3): Float3 {
        val turned = rotation(Quaternion.fromEuler(euler)) * Float4(vector.x, vector.y, vector.z, 0f)
        return Float3(turned.x, turned.y, turned.z)
    }

    @Test
    fun `поворот из домена разворачивает лицо модели к камере`() {
        // Лицо модели — ось +Z. Камера в любой стороне: после поворота лицо
        // должно смотреть ровно на неё по горизонтали.
        val cameras = listOf(
            Vec3(0.0, 1.0, 2.0),
            Vec3(2.0, 1.0, 0.0),
            Vec3(-1.5, 0.2, -1.5),
            Vec3(0.3, 2.0, -4.0),
            Vec3(-3.0, 1.0, 0.5),
        )
        cameras.forEach { camera ->
            val yaw = yawToward(camera)!!.toFloat()
            val face = rotate(Float3(0f, yaw, 0f), Float3(0f, 0f, 1f))
            val length = hypot(camera.x, camera.z)
            assertEquals("x, камера " + camera, (camera.x / length).toFloat(), face.x, EPS)
            assertEquals("z, камера " + camera, (camera.z / length).toFloat(), face.z, EPS)
            assertEquals("персонаж не кренится", 0f, face.y, EPS)
        }
    }

    @Test
    fun `отрицательный угол вокруг X уводит макушку за спину — это сальто назад`() {
        val head = rotate(Float3(-90f, 0f, 0f), Float3(0f, 1f, 0f))
        assertEquals(-1f, head.z, EPS)
        assertEquals(0f, head.y, EPS)
    }

    private companion object {
        const val EPS = 1e-4f
    }
}
