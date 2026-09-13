package ru.marshruty.ar.domain

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class SpriteClipTest {

    private val idle = SpriteClip(frameCount = 8, fps = 12, loop = true)
    private val trick = SpriteClip(frameCount = 24, fps = 24, loop = false)

    @Test
    fun `в нулевой момент показывается первый кадр`() {
        assertEquals(0, idle.frameAt(0))
        assertEquals(0, trick.frameAt(0))
    }

    @Test
    fun `кадры сменяются по частоте`() {
        // 12 кадров в секунду — новый кадр каждые ~83 мс.
        assertEquals(0, idle.frameAt(80))
        assertEquals(1, idle.frameAt(84))
        assertEquals(2, idle.frameAt(167))
    }

    @Test
    fun `петлевой клип идёт по кругу`() {
        val oneLoop = idle.durationMillis
        assertEquals(0, idle.frameAt(oneLoop))
        assertEquals(1, idle.frameAt(oneLoop + 84))
        assertEquals(0, idle.frameAt(oneLoop * 5))
    }

    @Test
    fun `непетлевой клип заканчивается и сообщает об этом`() {
        assertEquals(23, trick.frameAt(trick.durationMillis - 1))
        assertNull(trick.frameAt(trick.durationMillis))
        assertNull(trick.frameAt(trick.durationMillis + 5_000))

        assertFalse(trick.isFinished(0))
        assertTrue(trick.isFinished(trick.durationMillis))
    }

    @Test
    fun `петлевой клип не заканчивается никогда`() {
        assertFalse(idle.isFinished(idle.durationMillis * 100))
    }

    @Test
    fun `отрицательное время не роняет расчёт`() {
        assertEquals(0, idle.frameAt(-500))
    }

    @Test
    fun `длительность считается из числа кадров и частоты`() {
        assertEquals(1_000L, SpriteClip(frameCount = 24, fps = 24).durationMillis)
        assertEquals(2_000L, SpriteClip(frameCount = 24, fps = 12).durationMillis)
    }

    @Test
    fun `длительность округляется вверх когда кадры не делятся нацело`() {
        // 8 кадров при 12 к/с — это 666.67 мс. Усечение до 666 обрывало
        // последний кадр: петля не замыкалась, а трюк «доигрывался» раньше.
        val clip = SpriteClip(frameCount = 8, fps = 12, loop = true)
        assertEquals(667L, clip.durationMillis)

        val once = SpriteClip(frameCount = 8, fps = 12, loop = false)
        assertEquals(7, once.frameAt(once.durationMillis - 1))
        assertNull(once.frameAt(once.durationMillis))
    }

    @Test
    fun `трюк главнее речи`() {
        val action = resolveCompanionAction(
            trickElapsedMillis = 100,
            trickClip = trick,
            isSpeaking = true,
        )
        assertEquals(CompanionAction.TRICK, action)
    }

    @Test
    fun `после трюка персонаж возвращается к речи или покою`() {
        val afterTrick = trick.durationMillis + 1

        assertEquals(
            CompanionAction.TALKING,
            resolveCompanionAction(afterTrick, trick, isSpeaking = true),
        )
        assertEquals(
            CompanionAction.IDLE,
            resolveCompanionAction(afterTrick, trick, isSpeaking = false),
        )
    }

    @Test
    fun `без запущенного трюка действие определяет речь`() {
        assertEquals(
            CompanionAction.TALKING,
            resolveCompanionAction(null, trick, isSpeaking = true),
        )
        assertEquals(
            CompanionAction.IDLE,
            resolveCompanionAction(null, trick, isSpeaking = false),
        )
    }

    @Test
    fun `отсутствующий клип трюка не ломает выбор действия`() {
        assertEquals(
            CompanionAction.IDLE,
            resolveCompanionAction(trickElapsedMillis = 50, trickClip = null, isSpeaking = false),
        )
    }

    @Test(expected = IllegalArgumentException::class)
    fun `пустой клип отвергается`() {
        SpriteClip(frameCount = 0)
    }

    @Test(expected = IllegalArgumentException::class)
    fun `абсурдная частота кадров отвергается`() {
        SpriteClip(frameCount = 8, fps = 0)
    }
}
