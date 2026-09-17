package ru.marshruty.ar.domain

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import kotlin.math.abs

class FlipMotionTest {

    @Test
    fun `в начале и в конце персонаж стоит ровно`() {
        listOf(0f, 1f).forEach { p ->
            val t = flipTransform(p)
            assertEquals("подъём при p=$p", 0f, t.liftFraction, EPS)
            assertEquals("ширина при p=$p", 1f, t.scaleX, EPS)
            assertEquals("высота при p=$p", 1f, t.scaleY, EPS)
        }
        assertEquals(0f, flipTransform(0f).rotationDegrees, EPS)
    }

    @Test
    fun `оборот ровно один`() {
        // Не 359 и не 361: недокрут виден как кривая посадка.
        assertEquals(-360f, flipTransform(1f).rotationDegrees, EPS)
    }

    @Test
    fun `сальто идёт назад`() {
        // Отрицательный угол — макушка уходит от зрителя. Положительный дал бы
        // передний кувырок, а просили именно сальто назад.
        assertTrue(flipTransform(0.5f).rotationDegrees < 0f)
    }

    @Test
    fun `поворот только нарастает`() {
        var previous = 0f
        repeat(101) { step ->
            val current = flipTransform(step / 100f).rotationDegrees
            assertTrue("откат поворота на шаге $step", current <= previous + EPS)
            previous = current
        }
    }

    @Test
    fun `перед прыжком персонаж приседает`() {
        val crouch = flipTransform(0.08f)
        assertTrue("не сжался по вертикали", crouch.scaleY < 0.95f)
        assertTrue("не расширился по горизонтали", crouch.scaleX > 1.05f)
        assertEquals("подпрыгнул раньше времени", 0f, crouch.liftFraction, EPS)
        assertEquals("начал крутиться в приседе", 0f, crouch.rotationDegrees, EPS)
    }

    @Test
    fun `в верхней точке подъём максимален и тело вытянуто`() {
        val top = flipTransform(0.5f)
        assertEquals(1f, top.liftFraction, 0.02f)
        assertTrue("не вытянулся в полёте", top.scaleY > 1f)
        assertTrue("не сузился в полёте", top.scaleX < 1f)
    }

    @Test
    fun `приземление гасится приседом`() {
        val landing = flipTransform(0.93f)
        assertTrue("сел на прямых ногах", landing.scaleY < 0.95f)
        assertEquals("завис над землёй", 0f, landing.liftFraction, EPS)
    }

    @Test
    fun `масштаб не щёлкает на стыках фаз`() {
        // Присед, полёт и посадка — три отдельные формулы. Если хоть одна не
        // сходится с соседней в нуле, зритель видит рывок на переходе.
        var previous = flipTransform(0f)
        var maxJump = 0f
        repeat(1_001) { step ->
            val current = flipTransform(step / 1000f)
            maxJump = maxOf(
                maxJump,
                abs(current.scaleX - previous.scaleX),
                abs(current.scaleY - previous.scaleY),
                abs(current.liftFraction - previous.liftFraction),
            )
            previous = current
        }
        assertTrue("скачок $maxJump за один шаг из тысячи", maxJump < 0.01f)
    }

    @Test
    fun `выход за границы не ломает расчёт`() {
        assertEquals(flipTransform(0f).rotationDegrees, flipTransform(-3f).rotationDegrees, EPS)
        assertEquals(flipTransform(1f).rotationDegrees, flipTransform(9f).rotationDegrees, EPS)
    }

    private companion object {
        const val EPS = 1e-4f
    }
}
