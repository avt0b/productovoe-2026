package ru.marshruty.ar.domain

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class QrTriggerTest {

    @Test
    fun `без своего кода подходит любой прочитанный`() {
        assertTrue(qrTriggersCompanion(expected = null, scanned = "https://marshruty.ru/wp-2"))
        assertTrue(qrTriggersCompanion(expected = "  ", scanned = "что угодно"))
    }

    @Test
    fun `свой код срабатывает, чужой — нет`() {
        assertTrue(qrTriggersCompanion(expected = "wp-2", scanned = "wp-2"))
        assertFalse(qrTriggersCompanion(expected = "wp-2", scanned = "wp-3"))
    }

    @Test
    fun `лишние пробелы и регистр не решают, выйдет ли проводник`() {
        assertTrue(qrTriggersCompanion(expected = "wp-2", scanned = " wp-2\n"))
        assertTrue(qrTriggersCompanion(expected = " WP-2 ", scanned = "wp-2"))
    }

    @Test
    fun `пустой кадр не выводит проводника`() {
        assertFalse(qrTriggersCompanion(expected = null, scanned = null))
        assertFalse(qrTriggersCompanion(expected = null, scanned = ""))
        assertFalse(qrTriggersCompanion(expected = "wp-2", scanned = "   "))
    }

    @Test
    fun `перед человеком проводник ростом с ребёнка, а не по колено`() {
        // Таблички не было: мерить нечего, и прежние 35 см терялись в кадре.
        val inFront = companionHeightFor(
            explicitMeters = null,
            knownWidthMeters = null,
            measuredWidthMeters = null,
            placedInFront = true,
        )
        assertEquals(IN_FRONT_COMPANION_HEIGHT_METERS, inFront, 0.001f)

        val onMarker = companionHeightFor(
            explicitMeters = null,
            knownWidthMeters = null,
            measuredWidthMeters = null,
            placedInFront = false,
        )
        assertEquals(DEFAULT_COMPANION_HEIGHT_METERS, onMarker, 0.001f)
    }

    @Test
    fun `измеренная табличка важнее умолчания даже перед человеком`() {
        val height = companionHeightFor(
            explicitMeters = null,
            knownWidthMeters = 0.30f,
            measuredWidthMeters = null,
            placedInFront = true,
        )
        assertEquals(0.33f, height, 0.001f)
    }
}
